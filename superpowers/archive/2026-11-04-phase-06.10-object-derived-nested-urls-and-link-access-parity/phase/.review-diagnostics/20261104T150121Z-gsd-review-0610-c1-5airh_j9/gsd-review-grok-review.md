I'll verify each plan against the live source, starting with the URL, access, and delete paths the plans depend on.
## 06.10-01

### Summary

Plan 01 is source-grounded and is the right first cut. Today every sibling URL is forced through page kwargs, including falsey ones, and delete candidates stop at one parent. The shared resolver plus `cv_object` classification matches D-01–D-08, provided collection calls that still pass `obj` are not treated as object destinations.

### Strengths

- The current failure is real: `cv_get_router_and_args` copies page parent kwargs and raises when a value is missing or falsey (`src/crud_views/lib/view/base.py:598-603`). `if not value` rejects a valid parent pk of `0`.
- `reverse` uses kwargs only (`base.py:615-616`), while `args.reverse()` at `base.py:607` is the root-to-leaf tuple. Preserving that shape is necessary.
- Parent metadata is already declared, not guessed: `ParentViewSet.get_attribute` / `get_pk_name` (`src/crud_views/lib/viewset/parentviewset.py:56-66`). Resource-as-parent is already rejected (`src/crud_views/lib/viewset/__init__.py:216-225`).
- Classifying by `cv_object` is required. `get_success_url` always passes `obj` even for a list target (`base.py:244-246`), and breadcrumbs reverse the collection container with the page object (`src/crud_views/lib/breadcrumb.py:191-193`). Those must stay on page scope when it exists.
- Query bounds match Django FK behavior: a PK-targeted attname needs no load; a non-PK `to_field` does. The unmigrated test app has no migrations package, and `migrate` syncs those models, so the new models are a valid fixture approach.
- Optional mode is specified as a typed result, not `except ValueError`. That is the only way to satisfy D-12/D-14 given `ValueError` is also the public invalid-input type.

### Concerns

- **MEDIUM:** Breadcrumb ancestors are still URL-kwarg walks (`breadcrumb.py:223-232`) and are not in this plan’s files. On a stock scoped page they agree with the object. A custom `get_object` that renders Book B under Publisher A would emit an object crumb for B and ancestor crumbs for A. Call that limit out in the plan 05 docs, or ancestors will look like a resolver bug.
- **MEDIUM:** `LinkDetailColumnMixin.get_url` and `LinkChildColumn.render` bypass action assembly (`src/crud_views/lib/table/columns.py:42`, `columns.py:49-50`). Plan 01’s tracer only follows a detail action. One column render should be in the tracer so a later button-only change cannot miss the title/child links.
- **LOW:** Self-nesting is in the 01-02 behavior line, but the named models are Leaf → Child → Parent → Publisher only. Without a temporary self-FK, `parent_obj` disambiguation will be dropped.
- **LOW:** Reused pytest-django databases do not always pick up new unmigrated tables. The first metadata run may need `--create-db`. Registry cleanup must `pop` under `_REGISTRY_LOCK`, as `tests/test1/test_viewset.py:64` does; `ViewSet` construction also installs an auto manage view (`viewset/__init__.py:153-156`).

### Suggestions

- Make the 01-01 router change collection-safe immediately: no page kwargs and `cv_object is False` must not prefer `obj`. Do not wait for 01-02 to unbreak `get_success_url`.
- Assert normalized conflict on `0`, `""` is not a missing parent, and a same-pk parent from the other alias is not equal.
- Pin `clear_url_caches()` plus locked registry restore in the tracer fixture, not only in prose.

### Risk Assessment

**MEDIUM.** The contract matches the code. The main miss is callers that pass `obj` into a collection reverse, and column links that the tracer does not follow.

## 06.10-02

### Summary

The ContextVar seam is justified. `cv_has_access` is a two-argument classmethod (`base.py:398-399`, `base.py:1085-1088`; Guardian overrides at `src/crud_views_guardian/lib/mixins.py:85` and `mixins.py:143`). A new keyword would break application overrides. The plan correctly keeps request-free `ViewSet.get_url` free of ambient context and wraps the real render entries.

### Strengths

- Ordinary row/toolbar URLs go through `_cv_get_action_context` (`base.py:735-772`) and `cv_resolved_actions` (`base.py:663-673`). Table actions use that path (`src/crud_views/templates/crud_views/columns/actions.html:2`). Card inline and child actions are separate and are named (`src/crud_views/lib/views/card.py:57-87`).
- `ParentContextButton` and `SiblingContextButton` build URLs from page kwargs themselves (`src/crud_views/lib/view/buttons.py:159-169`, `buttons.py:286-288`) and must not be “fixed” by object ancestry. Sibling access is `obj=None` (`buttons.py:301`), which is the D-10 case.
- `cv_get_child_url` today writes only the immediate parent from `obj` and takes older ancestors from the page (`base.py:999-1003`). Deriving the whole chain from that parent object is the actual D-01 fix for child links.
- Create state already has its own page-parent resolver (`src/crud_views/lib/views/create.py:52-70`). Leaving it alone until plan 03 avoids breaking nested create while the carrier lands.
- Hook order is specified against the live extra-kwargs overwrite: class extras currently replace parent kwargs (`base.py:605`). Treating parent keys as constraints is a real behavior change and is testable.

### Concerns

- **MEDIUM:** `LinkChildColumn` calls `cv_get_child_url` directly (`columns.py:42`) and never enters the wrapped button/card scopes. URL logic is shared, but this plan’s “every location” claim is false unless that column is rendered once.
- **LOW:** A carrier miss that drops page kwargs would turn a collection row on page A into D-04 (derive from B). The getter text says it uses page scope; the mismatch tests should assert that, not only that the other task’s frame is absent.
- **LOW:** Thread and asyncio cases must not touch the Django connection. Isolation should be ContextVar-only.

### Suggestions

- Publish resolution inside `cv_get_router_and_args` / `cv_get_child_url`, then assert `LinkDetailColumn` and `LinkChildColumn` hrefs in `render_matrix`.
- On an open scope, a target/user/object mismatch should fail the test, not silently re-resolve. Silent fallback is an authorization bug if page A and row B differ.
- Keep `FilterContextButton`’s `cv_get_url(key=cv_key)` with no obj (`buttons.py:337`) in `navigation_preservation`. It is a collection reverse with no row.

### Risk Assessment

**MEDIUM.** The seam matches the signatures. Risk is an unwrapped URL caller or a fallback that drops page scope, not the ContextVar itself.

## 06.10-03

### Summary

This plan targets the two real access holes: core `cv_has_access` treats a missing permission as success, and Guardian link checks never apply the dispatch parent gate. The limited D-09/D-10 fallbacks match the current helpers. The plan is safe only if the new parent check stays on the immediate destination parent and create’s own override is updated, not merely `super()`’d.

### Strengths

- Core bug is exact: `permissions.get` miss becomes `has_perms(())`, which Django treats as allowed (`base.py:1085-1088`). The request path is a different function and already asserts with the migrate hint (`base.py:1062-1069`). Changing only the link helper preserves AUTH-08.
- Guardian object checks call `perm.split` with no declaration guard (`mixins.py:72`, `mixins.py:97`). Parent checks do the same (`mixins.py:360-368`). List `cv_has_access` ignores the permission entirely (`mixins.py:143-144`) and `get_queryset` passes that lookup straight into `get_objects_for_user` (`mixins.py:205-212`).
- Dispatch parent authority is immediate-only: `_guardian_check_parent` loads `parent_vs.get_pk_name()` and does not walk ancestors (`mixins.py:370-374`). “No ancestor gate” is not optional.
- Create does not use the parent mixin’s `cv_has_access`. `GuardianCreateViewPermissionRequired.cv_has_access` is its own method (`src/crud_views_guardian/lib/views.py:344-387`), and list rendering overwrites `cv_access` via `cv_create_has_access` (`mixins.py:167-191`). The plan names both.
- `_cv_guardian_create_parent` already swallows `ObjectDoesNotExist` (`views.py:292-295`). Replacing that with the typed resolver is the D-12 fix, and M2M own-child denial is already there (`views.py:290-291`).
- MRO is Parent before Object/Queryset (`views.py:245-247`). A cooperative `super()` from a new `GuardianParentPermissionMixin.cv_has_access` can sit in front of the child check without a new public access signature.

### Concerns

- **MEDIUM:** Opposite A/B grants are one-level publisher cases. They do not stop an implementation from checking every coordinate in the new chain. BookNote’s dispatch parent is Book, not Publisher. Add one case: publisher denied, book allowed, booknote link visible; and the reverse. That is the difference between this phase and a new ancestor policy.
- **MEDIUM:** Plan 04 runs in parallel and certifies links through `target._cv_cancel_target_available` (`src/crud_views/lib/views/delete.py:369`), which already calls `_guardian_user_has_parent_perm` and then `cv_has_access` (`mixins.py:257-262`). Removing the duplicate only in plan 03 changes hook counts under plan 04’s tests after merge. Plan 06 does not own either file.
- **LOW:** Declaration-before-inactive can turn an inactive request to a misconfigured Guardian view from `PermissionDenied` (`mixins.py:317-318`) into `ImproperlyConfigured`. Say which one the direct-request test expects.
- **LOW:** Resource viewsets with an empty `resource_permissions` map (`viewset/__init__.py:474-475`) use the same core helper. The undeclared matrix does not name them.

### Suggestions

- Put the declaration check in one helper used by core `cv_has_access`, Guardian object/queryset/parent, and create. Do not only patch `perm.split`.
- Test list/card `obj=None` toolbar links still follow D-10, and a resolvable row on the same page does not.
- Keep `_guardian_user_has_parent_perm` as the implementation and make `cv_guardian_has_parent_access` call it, so an existing override still runs from dispatch (`mixins.py:373`, `views.py:341`).

### Risk Assessment

**MEDIUM.** The defects are real and the policy order is right. The missing three-level parent test is the one that can ship a stricter policy than dispatch.

## 06.10-04

### Summary

Stock delete URLs are one level deep and then give up. Reusing `get_url(..., strict=False)` after the existing visibility filter, and leaving `_cv_get_protected_object_url` as a separate certifier, is the right split. This plan should not touch Guardian mixins.

### Strengths

- `cv_get_related_object_url` selects the first exact `viewset.model` detail and only copies one parent (`delete.py:192-210`). A BookNote under Book under Publisher cannot reverse today; `NoReverseMatch` becomes `None`.
- Visibility runs before URL work (`delete.py:443-448`). Cascade links use the public hook and skip certification (`delete.py:451-456`). The plan keeps that split.
- Certification already checks local path, script prefix, registered detail class, queryset, concrete pk type/value, and database (`delete.py:224-327`), then Guardian projection (`delete.py:332-369`). A resolver URL is not treated as permission. That matches D-08 and the 06.9 contract.
- Custom `cv_get_related_object_url` replaces the method, so strict=False inside the stock body does not swallow override errors. The certifier does not catch those exceptions (`delete.py:220`).
- File ownership is explicit: Guardian policy stays in plan 03. Temporary detail routes must not become the first registry match for an existing model; delete already filters registry entries for that reason (`tests/test1/test_delete.py:25-26`).

### Concerns

- **MEDIUM:** Parallel plan 03 edits the method certification calls. “Record a count change for plan 06” does not name an owner who may edit `delete.py` or `mixins.py` after both waves land. A merged failure has no task file list that includes both.
- **LOW:** `if parent_obj:` in the old helper (`delete.py:204`) is instance truthiness, not pk truthiness. Do not reintroduce it when reading explicit parent pks in the resolver.
- **LOW:** Exact `type(obj)` match skips subclass instances. That is current behavior. Polymorphic blockers stay text unless a test says otherwise. Do not “fix” that here.

### Suggestions

- After 03 and 04 both exist, run `test_delete.py` and `test_guardian_delete.py` once before plan 05, not only in plan 06’s full suite.
- Spy `cv_get_related_object_url` on a filtered-out protected row. The current filter replaces the instance with `None` (`delete.py:419-422`) before the URL loop; the spy must hook the filter, not only the URL method, or it will not prove hidden-first.
- Keep first-candidate failure as text. Do not scan the rest of `_REGISTRY` when the first detail is unavailable.

### Risk Assessment

**MEDIUM.** The delete integration itself is narrow and correct. The risk is the unowned merge with plan 03’s access composition.

## 06.10-05

### Summary

The docs plan matches D-16: this is Breaking, not a quiet Changed note, and the public names are exactly the three helpers the code will grow. Executable fences are the right bar. The stability page is a name list, not a method catalog, so the inventory has to be explicit or Phase 7 will not see the new surface.

### Strengths

- `docs/development/stability.md:9-16` says unlisted names are internal. `ViewSet.get_url` would be unofficial until 05-03 lists it. Listing the three helpers and marking `_ParentResolution` / `link_context` internal matches that rule (`stability.md:82-85` is the Guardian section to extend).
- Copied action templates consume `cv_url`; they do not rebuild parent kwargs (`tests/test1/app/templates/app/custom_edit_button.html:1`). Python recipes are the migration that matters. Template recipes from 06.9 should stay byte-stable, and this plan says not to rewrite them unless a behavior correction forces it.
- The documented error split matches the decision: `ValueError` for bad input, `NoReverseMatch` only from Django reverse. Unknown keys today raise `ViewSetKeyFoundError` (`viewset/__init__.py:342`). The plan’s request-free normalization has to be tested with `inspect.signature`, not a prose claim.
- Paired changelog and `docs/migrating-1.0.md` is the repo rule, and the old-call tracer (stale explicit parent raises, migrated call resolves) is the right proof.

### Concerns

- **MEDIUM:** The reference matrix must say collection reverses still receive `obj` from `get_success_url` and breadcrumbs, and that this is not an explicit conflict. If the docs tell callers to omit `obj` whenever a collection link is built, they will “fix” success redirects that are supposed to keep page scope.
- **LOW:** Measured query numbers cannot be copied from the research bounds. The plan says publish only measured figures. The task should fail if plan 01/03 summaries do not contain the actual counters yet.
- **LOW:** `stability.md` does not currently list methods. A class-only line for `ViewSet` does not freeze `get_url`. The inventory test must assert the method names, not only that the class heading exists.

### Suggestions

- Document the non-parity cases in one paragraph: unresolved M2M link can 403; `obj=None` toolbar/sibling links do not gain a parent gate; request dispatch remains immediate-parent only.
- State that `ViewSet.get_url` does not run a hosting instance’s `cv_get_router_and_args` override, while `CrudView.cv_get_url` does (`base.py:611-616`). The names are easy to mix up.
- Keep protected-delete recipe markers untouched and replay `test_delete_migration_docs.py`, as written.

### Risk Assessment

**LOW.** Docs are downstream of the code and the extraction test will catch a wrong snippet. The main miss is overstating collection/`obj` rules.

## 06.10-06

### Summary

The browser and gate plan is the right close. It refuses to reuse 06.9 evidence and it names the validator that would otherwise reject non-delete pages. It does not quite fit the current runner, and it cannot repair a plan 03/04 integration failure inside its own file list.

### Strengths

- `tests/browser/protected-delete.cjs:20` accepts only `smoke` and `all`. `validateEvidence` requires the protected case IDs and delete DOM keys for every case (`protected-delete.cjs:41-48`). The plan’s schema split is mandatory, not cosmetic.
- Hashes already bind source and recipes (`protected-delete.cjs:36-70`). Extending them to `docs/reference/buttons.md` is right because custom mode extracts those bodies.
- The 6.0 crispy-floor deselect of `test_filter_form_baseline` matches prior gates. The 4.2 command uses the normal `tests` session, not `crispy_floor`, so it should not copy that deselect.
- Preconditions block a missing Chromium or asset manifest from being recorded as a pass. That matches “missing browser evidence is not a unit-test pass.”
- Full `pytest tests -n 4` after both wave-3 plans is the right combined regression, including cancel, breadcrumb, and delete.

### Concerns

- **MEDIUM:** `git ls-files` (`protected-delete.cjs:36-37`) omits untracked `resolution.py` and `link_context.py`. Evidence can hash a tree that does not contain the new modules. Hash those paths explicitly, or require them to be tracked before `nested-smoke`.
- **MEDIUM:** `selection === 'all'` demands `screenshots/protected-${mode}-modal.png` beside the output file (`protected-delete.cjs:74-77`). `nested-all` writes `06.10-browser.json` and new `nested-*.png` names. Without a per-schema screenshot rule, the run fails or the old check is silently dropped.
- **MEDIUM:** `files_modified` is browser and planning artifacts only. The action says to repair integration defects through the owning task, but this wave has no permission to edit `mixins.py` or `delete.py`. A combined failure stops here.
- **LOW:** `nested-all` plus the old protected matrix in one browser process is long. Keep `nested-smoke` as the fast tracer; do not treat a smoke pass as the matrix.

### Suggestions

- Split validators: `smoke`/`all` stay delete-strict; `nested-smoke` checks same-row href and cleanup; `nested-all` checks A/B grants, hide/disable, and protected navigation with its own screenshot list.
- Record import paths for `crud_views.viewset.resolution` and `crud_views.view.link_context`, not only the package root, so a wheel install cannot satisfy the gate.
- If the combined delete/guardian replay fails, add a short fix task whose file list includes the two owners before writing ACCEPTANCE.

### Risk Assessment

**MEDIUM.** The gates are real and the old runner will reject a naive case addition. Evidence identity and the unowned merge are the gaps, not the scenario list.

## Cross-plan

The six plans implement the phase in the right order: one resolver, then render scope, then Guardian and delete consumers, then docs and a fresh browser gate. They match the live bugs: page-kwarg URLs (`base.py:598-603`), one-level delete candidates (`delete.py:201-205`), empty-permission link success (`base.py:1086-1088`), and Guardian `perm.split` / missing parent checks (`mixins.py:97`, `mixins.py:368-372`).

The phase is achievable. It is not low risk. Three gaps cut across plans:

1. Collection versus object must be `cv_object`, not “`obj` was passed.” Success, breadcrumbs, and filter URLs all pass an object into a collection reverse.
2. Guardian may check only the immediate destination parent. Dispatch does not walk ancestors (`mixins.py:370-372`). One-level A/B tests do not lock that.
3. Plans 03 and 04 are parallel, and plan 06 cannot edit either owner. Hook-count and parent-binding drift will show up only after merge.

**Overall risk: MEDIUM.** No plan invents a second resolver or a public `try_get_url`. Close the three gaps in the existing tasks before execution, rather than adding a seventh plan.
