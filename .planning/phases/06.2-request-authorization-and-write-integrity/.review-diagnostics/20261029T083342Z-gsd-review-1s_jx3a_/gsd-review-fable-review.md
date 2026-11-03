I've now traced every plan claim against the source, Django's and guardian's installed code in the cached nox environment, the templates, and the existing tests. Here is the review.

# Cross-AI Plan Review: Phase 6.2 (plans 06.2-01 … 06.2-06)

Repo access: full. All citations below were verified against the working tree at `introduce-gsd` and the installed packages in `.nox/crispy_floor-3-12-django-6-0` (Django 6.0.x, django-guardian 3.5.x, Pydantic 2.x).

Evidence baseline confirmed before reviewing the plans:

- B1 reproduces structurally: `django/views/generic/edit.py:220-228` (`DeletionMixin.delete`) loads the object, deletes and redirects. `src/crud_views/lib/views/delete.py:199-219` only guards `post()`. Nothing in `src/` overrides `delete()` or sets `http_method_names`.
- B2 reproduces for Guardian only: `src/crud_views/lib/formsets/mixins.py:37-45` returns the fragment before `super().get()`. `src/crud_views_guardian/lib/mixins.py:31-38` returns `True` from `has_permission()` for any authenticated user without calling `super()`, so `CrudViewPermissionRequiredMixin.has_permission()` (`src/crud_views/lib/view/base.py:900-911`, which calls `cv_get_action_object()` → `get_object()` and the state gate) never runs for Guardian object views. Core non-Guardian fragments *are* gated at dispatch by that same method.
- B3 reproduces: `src/crud_views_guardian/lib/views.py:46-50` passes `protected=related.protected` through unfiltered; `delete.py:172,184` does the same in core; `snippets/delete/related_objects.html:4-5` renders labels.
- B4/B6 reproduce: `mixins.py:232-234` returns before parent resolution (`:235`) and the state gate (`:244-245`); `views.py:146-149,195-198` compute `perm_key=None` → `permissions.get(None)` → `None.split()` at `:155,:204`.
- B5 is narrower than the plans assume (see 06.2-02).
- B7 reproduces: `viewset.py:23` declares the field, every runtime read is `getattr(self/cls, …)` on the view class (`mixins.py:43,66,168,224`, `views.py:45,150,199`), and `ViewSet` has no `model_config` (`src/crud_views/lib/viewset/__init__.py:47`), so Pydantic's default `extra="ignore"` silently drops unknown kwargs.

---

## 06.2-01

### Summary
The plan targets the right code (DELETE bypass, unfiltered `protected`, POST lifecycle) and its mechanism for the notice (`has_protected_objects` computed before filtering) is sound. It misses one template that gates the whole snippet on the very list it is about to empty, conflates two different "protected POST" behaviours, and asks for red-first evidence on tasks that are preservation tests.

### Strengths
- **Correct ordering for 405.** Restricting `http_method_names` lets `View.dispatch` reject DELETE only after `GuardianParentPermissionMixin.dispatch` (`mixins.py:196-202`, anonymous → redirect/403/404) and `PermissionRequiredMixin.dispatch` → `has_permission()` have run. Anonymous denial behaviour is preserved exactly as D-01's planning note requires.
- **Independent blocked flag is the right shape.** `delete.py:174-184` is the single projection point; capturing `bool(related.protected)` at `:180` before `:181` works for core and for Guardian (whose override replaces the method wholesale at `views.py:39-50` and never calls `super()`).
- **Guardian reuse of `_PermittedPks`** (`views.py:53-69`) is appropriate: it is already per-request and keyed by model, so applying it to `protected` costs one query per protected model.
- **Existing lifecycle tests to extend are real**: `tests/test1/test_transactions.py:308-331` (hook exception keeps row, on-commit runs) and `:373-384` (Guardian goes through the seam).

### Concerns
- **HIGH — the generic notice is lost in exactly the case D-08 names.** `src/crud_views/templates/crud_views/view_delete.content.html:8` reads `{% if related_summary or protected_objects %}` before including `related_objects.html`. In a protected-only collection (e.g. Publisher with a PROTECT Contract and no cascade children, `tests/test1/app/models.py:72-73`), `NestedObjects.collect` aborts on the first `ProtectedError`, so `summary` is `{}`. Once `protected_objects` is filtered to `[]`, the include is skipped and `has_protected_objects` is never read. `view_delete.content.html` is not in `files_modified`.
- **MEDIUM — "protected POST preserves the row" means two different things.** Existing protection tests use `cv_check_delete_protection()` (`tests/test1/app/views.py:812`), which re-renders with 200 (`delete.py:206-214`). A DB-level PROTECT has no handler anywhere in `src/` (`grep ProtectedError src/` is empty), so a confirmed POST raises `ProtectedError` out of `cv_form_valid` (`delete.py:222`) and the test client re-raises. The tracer's behaviour statement does not say which case it asserts. If the executor writes the DB-PROTECT variant expecting 200, it fails for a reason unrelated to this phase, and "handle ProtectedError" would be scope creep.
- **MEDIUM — existing tests will break and the plan does not name them.** `tests/test1/test_delete.py:150` asserts `len(context["protected_objects"]) > 0` for `client_user_publisher_cascade_delete`, who has no `view_contract` permission. After filtering it becomes `[]`. `tests/test1/test_guardian_delete.py:46-52` asserts the empty-tree early return returns `related` *by identity*; 01-02 removes that return.
- **LOW — the "empty-tree early return bypasses protected filtering" rationale is not what happens on a request.** `NestedObjects.collect` calls `add_edge(None, obj)` for the root before delegating, and `nested()` iterates `edges[None]`, so `related.tree` always contains at least the root object. The early return at `views.py:42-43` is only reachable from direct calls. The real leak is line 49. Removing the early return is still fine, but the justification in the task should be corrected so the executor does not go looking for a request-level repro of it.
- **LOW — Guardian DELETE from an ungranted user becomes 405, not 403.** Today the object check runs inside `DeletionMixin.delete()` via `get_object()`. After `http_method_names` restriction, `View.dispatch` returns 405 before any handler, for every authenticated user and every pk. That is acceptable (no object information is disclosed), but the truth "existing denial behavior remains intact" should be read as "for anonymous users"; tests should expect 405 for authenticated actors regardless of grant.
- **LOW — acceptance boilerplate.** 01-03 is a preservation task (validation, hooks, rollback already pass per `test_transactions.py`), yet its acceptance criterion requires "new regressions must fail against the old behavior". Only the repeated-DELETE case can be red-first.

### Suggestions
- Add `view_delete.content.html` to `files_modified` and change line 8 to `{% if related_summary or has_protected_objects %}`; add a test for protected-only + zero visible labels that asserts both the context flag and one `alert-danger`.
- State explicitly in 01-01 that "protected POST" means `cv_check_delete_protection`; add a one-line note that DB-level `ProtectedError` on confirmed POST is pre-existing behaviour, out of scope.
- List `test_delete.py:142-153` and `test_guardian_delete.py:46-52,54-73` as tests to update.
- Pin the method restriction with an explicit test on both the core and the Guardian route and an `Allow` header check on OPTIONS (cheap, and proves the restriction is declarative).

### Risk Assessment
**MEDIUM.** The security fix is straightforward and well located; the HIGH item is a one-line template fix but it would otherwise falsify D-08 in the most sensitive case.

---

## 06.2-02

### Summary
The parent-None analysis is correct and the proposed fix sits at the right seam. The inactive-user task overstates the defect: guardian's object checker already denies inactive users, so only the queryset paths leak. As written, the plan's red-first requirement cannot be met for most of the listed gates.

### Strengths
- **B4 root cause confirmed.** `mixins.py:232-234` returns on `perm_key is None` before `get_object_or_404` at `:235` and the no-object state gate at `:244-245`. Because `GuardianParentPermissionMixin.has_permission()` returns `True` whenever a parent exists (`:191-194`), `CrudViewPermissionRequiredMixin.has_permission()`'s own state gate (`base.py:900-911`) is also skipped, so the dispatch gate is the only place left to enforce state. Fixing it there is right.
- **B6 root cause confirmed** at `views.py:146-149` and `:195-198`; the `or` chain yields `None` → `permissions.get(None)` → `None.split()`. A shared classmethod resolver used by `_guardian_parent_perm_key()` (`mixins.py:212-218`) and both helpers removes the triplicate logic.
- **Inactive-session test design is sound.** `client.force_login(user, backend="django.contrib.auth.backends.AllowAllUsersModelBackend")` keeps an inactive user authenticated because `get_user()` honours the backend's `user_can_authenticate()`. The default backends in `tests/test1/conftest.py:104-107` would mask the defect, as the plan says.
- **Parent-binding tests have precedent**: `tests/test1/test_guardian.py:375-389` (`_make_book_list_view`) and `:540-563` compare `cv_access`/`cv_action_enabled` across the real and aliased create buttons.

### Concerns
- **MEDIUM — B5 is a queryset-path defect, not an everywhere defect.** `guardian/core.py:76` (`ObjectPermissionChecker.has_perm`) returns `False` when `not self.user.is_active`, and `ModelBackend.has_perm` returns `False` for inactive users. So `GuardianObjectPermissionMixin.get_object()` (`mixins.py:50-58`), `_guardian_has_parent_perm()` (`:220-228`) and both create helpers already deny inactive actors in strict *and* global-fallback mode. The only leaking paths are `get_objects_for_user`, which returns the full queryset for superusers at `guardian/shortcuts.py:679` and never consults `is_active` for object grants: `mixins.py:159-170`, `viewset.py:63-73`, and `_PermittedPks` at `views.py:61-69`. The task's acceptance criterion ("new regressions must fail against the old behavior") is unsatisfiable for detail/update/delete/action/create/fragment entry, and an executor may waste a cycle hunting a red that does not exist or, worse, misread the existing 403 as a false negative.
- **LOW — `has_permission()` return value for inactive.** The plan says "for authenticated inactive requests use PermissionDenied". Returning `False` from `has_permission()` already yields 403 for authenticated users via `AccessMixin.handle_no_permission()`; raising is equivalent but bypasses `cv_guardian_anonymous_behavior` semantics only for anonymous, which is not this case. Either is fine; say which, so core and Guardian tests assert the same status.
- **LOW — `cv_has_access` case 2** (`views.py:190-191`) returns `False` for `obj=None` on purpose; after the resolver change it must keep doing so, or the list page's `cv_get_context` re-derivation at `mixins.py:130-155` becomes dead. Not stated.

### Suggestions
- Split 02-02 into (a) red-first regressions on the three queryset paths plus inactive superuser, and (b) green-first pinning tests on the object/parent/helper paths, with the prose explicitly crediting guardian's checker. Keep the defensive `is_active` gates if desired, but do not require them to flip a test.
- In 02-01 add the concrete expected statuses for the None policy: enabled → 200/302 with no grants; disabled → 403 on GET and POST; missing parent → 404; and assert `Book.objects.filter(title=...)` absence for the disabled POST.

### Risk Assessment
**MEDIUM.** Code changes are small and well located. The risk is procedural: the plan's own evidence rule contradicts guardian's actual behaviour, which can stall execution or produce fabricated red evidence.

---

## 06.2-03

### Summary
03-01 attacks the real B2 defect at the right place with the right fixture shape. 03-02's persisted-ancestry validator buys little confidentiality because fragments never load instance data, while carrying real risk of breaking the shipped JS contract. The plan should narrow 03-02 to grammar and root identity unless the maintainer explicitly wants DB ancestry checks.

### Strengths
- **Correct scoping of the authorization gap to Guardian.** Core `UpdateViewPermissionRequired` already runs `cv_get_action_object()` → `get_object()` (404 for missing pk) and the state gate at dispatch (`base.py:900-911`). Guardian short-circuits that (`mixins.py:31-38`), so the Guardian update fixture with a secret `ModelChoiceField` is the discriminating case, as the plan says.
- **The fix mirrors existing code.** Setting `self.object = self.get_object() if self.cv_object else None` before `get_template_html()` copies `src/crud_views/lib/views/mixins.py:37` and reuses the cooperative `get_object()` chain, so Guardian's object + state gate (`mixins.py:50-58`) applies to fragments with no new permission logic.
- **Polymorphic compatibility is already implied**: `PolymorphicFormSetsViewMixin.cv_get_formsets()` reads `self.polymorphic_model` (`src/crud_views_polymorphic/lib/utils.py:49-56`), which for update views already calls `get_object()` at `:44`.
- **Existing 400 tests to extend are real** (`tests/test1/test_formsets_bugs.py:107-142`), and the request shape is documented (`docs/reference/formsets.md:140-146`).

### Concerns
- **MEDIUM — 03-02 over-reaches relative to the threat.** `FormSet.template()` builds `self.klass(formset=self, prefix=prefix)` with no `instance` and no `queryset` (`formsets.py:192-193`), so the rendered rows are blank extra forms. A forged `pk` or `formset_parent_prefix_key` only changes prefix strings in the HTML; no data belonging to the forged ancestor is read. On POST, `FormSet.init()` rebuilds prefixes from the real tree (`formsets.py:120-124,150,165`), so a forged prefix is simply never bound. Querying persisted ancestry on every add-row click adds DB work and new failure modes for a confidentiality gain of zero.
- **MEDIUM — JS contract fragility.** `src/crud_views/static/crud_views/js/formset.js:319-323` sends `pk: "None"` or the inline parent's pk, `num: get_total_forms()`, and `formset_parent_prefix_key: this.formset.parent_prefix_key`, which is `null` for top-level formsets (`render_tree.py:135-137`) and is serialized by jQuery as an empty string. A validator that rejects an empty prefix key for level 0, or rejects `num` greater than the current row count, breaks every first-level add. The plan mentions the right exceptions (None sentinel, new indices, UUID hyphens), but the acceptance test list does not include "top-level add on an unsaved create page with the real JS parameter set".
- **LOW — the prefix grammar is per-level `{pk}-{index}-{form_index}` where `pk` may be a UUID.** `FormSet.PK.UUID` (`formsets.py:29`) exists, but there is no UUID inline fixture in `tests/test1/app/views_formset.py`; the plan correctly defers that to test-local declarations.
- **LOW — fixture registration.** Guardian ViewSets register globally by name (`_REGISTRY`); module-level test fixtures must use unique names and the test module must set `ROOT_URLCONF` (default `tests.test1.project.urls`, `conftest.py:74`) and clear URL caches. The plan says "temporary URLConf" but not cache clearing.

### Suggestions
- Keep 03-01 as is. Re-scope 03-02 to: (1) `pk` matches the declared `FormSet.PK` regex or is `None`; (2) for level 0, `pk` equals `self.object.pk` (or `None` on create); (3) `formset_parent_prefix_key` is empty for level 0 and matches `^(pk|None)-\d+-\d+(?:-(pk|None)-\d+-\d+)*$` for deeper levels, with `pk` being the declared grammar. Drop DB ancestry lookups or make them an explicit maintainer decision recorded in CONTEXT.
- Add one positive test per real JS parameter set: top-level add on create (`pk=None`, empty prefix key), top-level add on update, nested add under a persisted row, nested add under a client-added unsaved row.

### Risk Assessment
**MEDIUM.** 03-01 is low risk and high value. 03-02 is the single most regression-prone task in the phase for the least security return.

---

## 06.2-04

### Summary
The removal and diagnostic are well targeted and the Pydantic mechanism is right. The task split leaves the manage view broken between 04-01 and 04-02 with a verify command that cannot see it.

### Strengths
- **Correct Pydantic diagnosis.** No `model_config` on `ViewSet` (`viewset/__init__.py:47`) → unknown kwargs are discarded. A `mode="before"` validator sees the raw mapping; the analog at `formsets.py:270-277` is exactly the right pattern, and `GuardianViewSet` already has an `after` validator (`viewset.py:35-49`) so adding a `before` one is idiomatic.
- **Low blast radius in-repo.** No file under `examples/`, `docs/` or `tests/` passes `cv_guardian_accept_global_perms=` to `GuardianViewSet(...)`; every test sets it on a view class (`test_guardian.py:230-238,832,842,861,874,886,897,916`). The only readers of the ViewSet field are `views.py:231` and the manage template.
- **Manage gate untouched** (`manage.py:30-39`); per-view enrichment has a precedent at `views.py:270-276`.
- **D-05 preserved**: `viewset.py:67-73` hardcodes `accept_global_perms=False, use_groups=True`; the plan changes only the inactive handling from 02.

### Concerns
- **MEDIUM — intra-plan ordering breaks manage between tasks.** 04-01 removes `viewset.py:23`; `GuardianManageView.get_context_data` still reads `self.cv_viewset.cv_guardian_accept_global_perms` at `views.py:231` until 04-02. Every Guardian manage request raises `AttributeError`, and `tests/test1/test_guardian.py:636-655` goes red, but 04-01's `<verify>` runs only `test_guardian_policy.py`, so the tracer gate passes on a broken tree.
- **LOW — `data` may not be a mapping in a before-validator.** `check_keys` at `formsets.py:272-273` assumes a dict. Guard with `isinstance(data, dict)` so model instances or `model_validate` from objects do not crash with a misleading error.
- **LOW — "applicability" needs a concrete rule.** `get_view_data()` iterates `get_all_views()`, which includes the manage view itself and top-level create views, neither of which reads the flag. Plan 04-02 says "avoid implying…" but does not define the three states (strict / global-accepting / not applicable). Phase 7 will freeze whatever names appear here.

### Suggestions
- Move the one-line `views.py:231` change (and the template row) into 04-01, or make 04-01's verify include `tests/test1/test_guardian.py`.
- Define the manage row values explicitly, e.g. `effective_global_perms: True | False | None` plus a human label, and the fixed strict-helper entry `get_objects_for_user: strict (accept_global_perms=False, use_groups=True)`.
- Add a constructor test for `GuardianViewSet(model=..., name=..., unrelated_extra=1)` to prove unrelated extras keep their existing behaviour (D-04 scope limit).

### Risk Assessment
**LOW–MEDIUM.** Mechanically simple; the only real hazard is the task-boundary breakage.

---

## 06.2-05

### Summary
A pure test plan that replays the actor matrix after all fixes land. It is the right place for D-12 coverage, but its acceptance boilerplate is impossible by construction, and it inherits 03's fixture approach without specifying the URLConf mechanics.

### Strengths
- **All referenced modules exist**: `test_conditional_formset.py`, `test_crud.py`, `test_cancel_origin.py`, `test_form_buttons_golden.py` with both `test_filter_form_baseline` (`:266`) and `test_filter_form_controls_match_golden` (`:275`); the `--deselect` matches `noxfile.py:57` exactly.
- **The locmem override fixture is a faithful analog** (`tests/test1/test_crispy_buttons.py:354-375`): deep-copied `TEMPLATES`, `APP_DIRS=False`, locmem first.
- **Context assertions, not just HTML**, are required throughout, which is what the source note's "do not treat green suites as coverage" demands.
- **Aggregate purge authority** is preserved by including the conditional-formset selection rather than re-testing it.

### Concerns
- **MEDIUM — red-first is impossible in wave 4.** Both tasks' acceptance criteria require "new regressions must fail against the old behavior before the fix". By wave 4 every fix is merged; the only way to satisfy it is to revert production code temporarily, which the plan does not authorize. This will either stall the executor or produce invented evidence.
- **LOW — Guardian DELETE expectation.** Per 06.2-01, authenticated actors receive 405 regardless of grant; the matrix row "ungranted actor sends DELETE" must expect 405, not 403.
- **LOW — URLConf isolation.** The plan says "test-local route approach of 03" but neither plan states `override_settings(ROOT_URLCONF=...)` + `clear_url_caches()`; registering new Guardian ViewSets also permanently extends the global registry for the session, which can affect `cv_get_related_object_url()` (`delete.py:98-116`) in other tests if a test-local ViewSet registers a `detail` view for `Publisher`.
- **LOW — VALIDATION.md drift.** The 06.2-05-02 row (`06.2-VALIDATION.md:43`) omits the `--deselect` that the plan's verify includes; at the crispy floor that row fails.

### Suggestions
- Replace the acceptance boilerplate with "each matrix cell has a discriminating assertion that would fail if the corresponding gate were removed" and, optionally, one mutation spot-check per plan (comment out the gate, observe red, restore).
- Name the URLConf mechanism and require test-local ViewSets to use models without a registered core `detail` view, or to avoid registering `detail`.

### Risk Assessment
**LOW–MEDIUM.** No production risk; moderate execution risk from the unsatisfiable criterion.

---

## 06.2-06

### Summary
Documentation and evidence recording are complete in scope and correctly paired with the Breaking rule in `CLAUDE.md:105`. The full-suite-at-crispy-floor requirement is unmeasured and may surface unrelated failures.

### Strengths
- **Tooling exists**: `.venv/bin/mkdocs` and both `.nox/crispy_floor-3-12-django-{4-2,6-0}` are present; `CHANGELOG.md:7` already has the Unreleased `### Breaking` block and `docs/migrating-1.0.md` has the section structure to extend.
- **Right documents chosen.** `docs/reference/delete_view.md:128-135` ("Permission Filtering") currently claims no leak and must gain the protected-label and `has_protected_objects` contract; `docs/reference/guardian.md:168-185` describes the None policy and the per-view flag; `guardian.md:242` lists the flag in a reference list that will need the ViewSet/view distinction.
- **Phase 7 handoff is explicit** and names each new contract (method restriction, diagnostic, two context keys, manage rows, strict helper, fragment validation).

### Concerns
- **MEDIUM — "full tests/test1 in both environments" is not an existing documented gate.** `noxfile.py:96-106` runs only `CRISPY_FLOOR_TESTS` at the floor pins; the full suite is run by the `tests` session with current crispy. Nothing in RESEARCH or VALIDATION shows the full suite green at the floor. Unrelated whitespace-bound goldens may fail and the task forbids converting them to passes, which could block ACCEPTANCE sign-off for reasons outside this phase.
- **LOW — acceptance boilerplate on docs tasks.** 06-01 and 06-02 require "Run the named test selection… new regressions must fail against the old behavior" while their verify is `mkdocs build --strict`.
- **LOW — migration wording risk.** The plan says "describe access fixes accurately without suggesting global permissions now inherit"; it should also state that DELETE was never a documented API (no doc mentions HTTP DELETE), so the Breaking entry is about an inherited Django behaviour, not a removed feature.

### Suggestions
- Run the full-suite-at-floor command once *before* execution and record the baseline; if it is not green, scope 06-03 to the documented floor selection plus `pytest tests` in `.venv`, and say so in ACCEPTANCE.
- Strip the test-selection sentence from the two docs tasks.

### Risk Assessment
**LOW.** Documentation risk only; the measurement scope needs a baseline.

---

## Cross-plan observations

- **Systemic boilerplate defect (MEDIUM).** Every task in all six plans carries "new regressions must fail against the old behavior before the fix", including preservation tasks (01-03), already-secure paths (02-02 object gates), post-fix replay (05-*), and docs builds (06-01/02). This should be fixed in the plan generator or edited per task before execution; it is the most likely cause of stalled or fabricated evidence.
- **Dependency ordering** is otherwise sound: 03 and 04 share wave 3 with disjoint files; 01→02 serialize `crud_views_guardian/lib/views.py`; the only ordering hazard is inside plan 04 (manage breakage between tasks).
- **Scope and over-engineering**: 03-02's persisted-ancestry validation is the one item that exceeds the demonstrated threat; everything else is tightly scoped to B1–B7.
- **Security**: no plan introduces new attack surface. 405-before-object-check on Guardian delete routes discloses nothing. Removing the ViewSet flag cannot loosen access because nothing ever read it.
- **Performance**: `_PermittedPks` on protected objects adds one query per protected model per preview; fragment ancestry checks (if kept) add one query per nesting level per add-row click.
- **Goal achievement**: with the HIGH item in 06.2-01 fixed, the six plans achieve all seven roadmap criteria. Without it, criterion 3 ("deletion remains visibly blocked even if all labels are hidden") fails in the protected-only case.

## Overall risk assessment

**MEDIUM.** The plans correctly diagnose every finding against current source and place fixes at the right seams. Three things must change before execution: add `view_delete.content.html` to plan 01, narrow or explicitly re-decide 03-02, and remove the uniform red-first acceptance clause where it cannot apply. The remaining items are small wording and ordering fixes.
