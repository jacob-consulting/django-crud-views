# Cross-AI Plan Review — Phase 06.3 (`1a82767`, Cycle 1)

**Scope reviewed:** `.planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/` (`06.3-CONTEXT.md`, `06.3-RESEARCH.md`, `06.3-DESIGN.md`, `06.3-PATTERNS.md`, `06.3-VALIDATION.md`, and `06.3-01-PLAN.md` through `06.3-09-PLAN.md`) against tracked repository source, tests, docs, and `noxfile.py`.
**Note on `DEL-01`:** This review evaluates plan quality, technical soundness, and task executability. It does **not** satisfy the `DEL-01` / `D-16` maintainer design-approval gate in `06.3-01`.

---

## 06.3-01

### Summary
Establishes Wave 1 blocking human checkpoints before any production or test code is written: `01-01` records maintainer approval of `06.3-DESIGN.md` (with SHA-256 digest binding) in `06.3-APPROVAL.md`, and `01-02` records human verification of the `SUS`-flagged PyPI packages (`Django`, `django-guardian`, `pytest`, `pytest-django`) in `06.3-PACKAGES.md` before `09-01` provisions the missing Django 5.2 nox environment.

### Strengths
- **Hard pre-implementation gate (`DEL-01`, `D-16`):** `06.3-01-PLAN.md:19-33` binds `06.3-APPROVAL.md` to `hashlib.sha256((p/"06.3-DESIGN.md").read_bytes()).hexdigest()`, preventing downstream waves (`06.3-02` depends on `06.3-01`) from executing against an unapproved or silently altered design.
- **Supply-chain isolation (`T-06.3-SC`):** Separates offline iteration on existing cached interpreters (`.nox/crispy_floor-3-12-django-4-2` and `6-0`) from fresh package installation required by `noxfile.py:6-19` (`tests-3.12(django='5.2')`).

### Concerns
- **[MEDIUM] `06.3-DESIGN.md` SHA-256 check (`C0101`) is fragile if later waves append evidence to `06.3-DESIGN.md`:**
  `06.3-01-PLAN.md:72` and `06.3-VALIDATION.md:54` assert `hashlib.sha256((p/"06.3-DESIGN.md").read_bytes()).hexdigest() in a`. Meanwhile, `06.3-DESIGN.md:107` states *"Maintain upstream attribution and a source-comparison table in the implementation evidence."* If an executor during `06.3-04` or `06.3-09` edits `06.3-DESIGN.md` to add the Django 4.2/5.2/6.0 `Collector` comparison table instead of placing it in `06.3-04-SUMMARY.md` or `06.3-MATRIX.md`, `C0101` will fail retroactively.
- **[LOW] Unspecified read-only dependency resolution command in `01-02`:**
  `06.3-01-PLAN.md:88` instructs the executor to *"Resolve the existing nox `tests-3.12(django='5.2')` dependency set without installing it"* to list any transitive or extra packages from `pyproject.toml:26-83` (`noxfile.py:13-14` installs `django~=5.2.0` and `.[polymorphic,workflow,ordered,test]`). Because `pip` is absent in the probed environments (`06.3-RESEARCH.md:135`), the task should name the exact read-only `uv` command (e.g. `uv pip compile pyproject.toml --extra polymorphic --extra workflow --extra ordered --extra test`) so the executor does not trigger a virtualenv install before the checkpoint completes.

### Suggestions
- Explicitly state in `01-01` and `04-01` that `06.3-DESIGN.md` is frozen once `06.3-APPROVAL.md` is written, and that the `_DeleteCollector` upstream comparison table belongs in `06.3-04-SUMMARY.md` / `06.3-MATRIX.md`.
- Specify the exact non-installing `uv` resolution command in `01-02`.

### Risk Assessment
- **Risk Level:** Low. Checkpoint-only plan with no repository source modifications.

---

## 06.3-02

### Summary
Implements the Wave 2 end-to-end tracer (`02-01`) and callback-safety regression suite (`02-02`): creates `src/crud_views/lib/deletion.py`, moves and re-exports `RelatedObjects`, wires callback-free `inspect_deletion()` into `DeleteView.get_context_data()`, wires `execute_deletion()` and delete-scoped alias pinning into `DeleteView`, updates the delete templates to show the incomplete-preview warning, and adds real-preview callback-event regressions in `tests/test1/test_delete_inspection.py` and `tests/test1/test_delete.py`.

### Strengths
- **Eliminates premature callback execution (`CR-02`, `DEL-02`):** Replaces `NestedObjects(using=using)` + `collector.collect([self.object])` in `src/crud_views/lib/views/delete.py:212-214`, which currently executes `SET(...)` callables, `SET_DEFAULT` factories, and custom `on_delete` handlers on every `GET` and invalid/blocked `POST`.
- **Preserves public tuple and import compatibility:** Moving `RelatedObjects` (`src/crud_views/lib/views/delete.py:33-36`) to `crud_views.lib.deletion` while re-exporting it from `crud_views.lib.views.delete` preserves `from crud_views.lib.views.delete import RelatedObjects` in `src/crud_views_guardian/lib/views.py:49` and existing `cv_filter_related_objects` overrides (`delete.py:275-302`).
- **Template branch independence (`D-03`, `D-12`):** Places the incomplete-preview alert in `src/crud_views/templates/crud_views/view_delete.content.html` outside the `{% if delete_protection_errors %}` and `{% if related_summary or has_protected_objects %}` guards (`view_delete.content.html:5-10`), ensuring visibility even when `cv_show_related_objects=False` or custom protection errors exist.

### Concerns
- **[HIGH] `C0202` runs `tests/test1/test_delete.py`, which contains tests that directly import removed functions and rely on `cv_get_related_objects` monkeypatching to simulate stale previews:**
  `06.3-02-PLAN.md:94` says: *"Do not erase old propagation coverage: move obsolete internal classifier assertions to the new origin cases in 04 while retaining existing behavior controls."*
  However, `C0202` (`06.3-02-PLAN.md:98`) runs `pytest tests/test1/test_delete_inspection.py tests/test1/test_delete.py` at the end of Wave 2 (before Wave 4's `06.3-04` runs):
  1. `tests/test1/test_delete.py:1143,1187,1220,1257,1295,1321,1364,1381` directly import `_cv_has_native_collection_graph` and `_cv_is_target_collection_protection` from `crud_views.lib.views.delete` (`src/crud_views/lib/views/delete.py:43-126`). If `02-01` removes those functions from `delete.py` in Wave 2, `test_delete.py` will fail with `ImportError` during `C0202`.
  2. `_delete_probe` (`tests/test1/test_delete.py:789-806`) and `test_delete_native_target_backstop_keeps_storage` (`test_delete.py:1403-1439`) create a `Contract`/`Royalty` protector *before* `client.post(...)` and monkeypatch `view.cv_get_related_objects` to return `RelatedObjects([], {}, [])` (`lines 796, 1421`) so that `get_context_data()` sees `has_protected_objects=False` and enters `cv_form_valid_process()` (`src/crud_views/lib/views/delete.py:344-350`). Once `02-01` changes `get_context_data()` to call `inspect_deletion()` instead of `self.cv_get_related_objects()`, `get_context_data()` will detect the `Contract`/`Royalty` during the precheck (`has_protected_objects=True`), returning early at `delete.py:348`! As a result:
     - `test_delete_callable_relationship_default_propagates_after_real_commit` (`test_delete.py:1215-1247`), `test_delete_unknown_collection_loader_propagates_after_real_commit` (`test_delete.py:1252-1276`), and `test_delete_unknown_collector_type_propagates` (`test_delete.py:1444-1469`) will **fail** in `C0202` because `post()` returns a 200 blocked response at line 348 instead of entering `cv_form_valid` and raising `ProtectedError`/`RestrictedError`!
     - `test_delete_native_target_backstop_keeps_storage` (`test_delete.py:1403-1439`) will pass `status_code == 200/422` via the early precheck at line 348 without ever reaching `try: self.cv_form_valid_process(context) except _NativeDeleteBlocked:` (`delete.py:350-353`), and `assert preview_calls == [target.pk]` (`line 1436`) will fail!
- **[MEDIUM] `inspect_deletion` tree structure must match `NestedObjects.nested()` for `_build_display_tree` and `_walk_nested`:**
  In `src/crud_views/lib/views/delete.py:222,247-273`, `NestedObjects.nested()` returns `[root_obj, [child_1, [grandchild_1], child_2]]` where a parent instance at index `i` is immediately followed at `i + 1` by a nested `list` of its children (`delete.py:266`). `02-01` and `03-01` must ensure `inspect_deletion` produces this exact flat-paired list shape (including the root object and `cv_filter_related_objects` replacing unpermitted nodes with `None`, see `tests/test1/test_guardian_delete.py:235-244`).
- **[MEDIUM] `DeleteView.cv_get_db_alias` fallback when `self.object` is not set:**
  `06.3-DESIGN.md:119` specifies `router.db_for_write(type(self.object), instance=self.object)`. If `cv_get_db_alias()` is called on a bare view instance before `self.object` is bound (as in `tests/test1/test_transactions.py:48-54`) or when `getattr(self, "object", None)` is `None`, `type(self.object)` would pass `NoneType` to the router. It should fall back to `self.cv_viewset.model` when `getattr(self, "object", None) is None`.
- **[MEDIUM] Pinning `cv_get_delete_db_alias()` before `cv_form_valid` when `cv_atomic=False`:**
  In `src/crud_views/lib/view/base.py:244-246`, `cv_get_atomic()` returns `nullcontext()` when `self.cv_atomic` is `False` without calling `cv_get_db_alias()`. In `src/crud_views/lib/views/mixins.py:54-57`, `cv_form_valid_process` runs `self.cv_form_valid(context)` (which deletes `self.object` and clears `self.object.pk = None`) before `transaction.on_commit(..., using=...)`. Therefore, `DeleteView.cv_form_valid_process` must call `using = self.cv_get_delete_db_alias()` *before* `self.cv_form_valid(context)` so the alias is guaranteed to be pinned while `self.object.pk` is still non-null even if `cv_form_valid_process` is called directly with `cv_atomic=False`.

### Suggestions
- In `02-02`, update `_delete_probe` and the stale-preview tests in `tests/test1/test_delete.py:789-1469` (e.g., by injecting the protector in `cv_post_hook` *after* `get_context_data()` has already inspected the unblocked target, or via the private inspection seam) and migrate the direct `_cv_has_native_collection_graph` unit tests in `02-02` so `C0202` passes cleanly at the end of Wave 2.
- Guard `DeleteView.cv_get_db_alias()` for `getattr(self, "object", None) is None` and pin `using = self.cv_get_delete_db_alias()` at the start of `DeleteView.cv_form_valid_process`.

### Risk Assessment
- **Risk Level:** High (due to `C0202` running `test_delete.py` where `_delete_probe` and `_cv_has_native_collection_graph` are tightly coupled to the removed implementation).

---

## 06.3-03

### Summary
Expands `inspect_deletion` in `src/crud_views/lib/deletion.py` to cover the full native relationship matrix (cycles, diamonds, `RESTRICT` cascade-closure reconciliation, multi-table parents, auto-created M2M through models, generic/private relation boundaries), adds `cv_get_delete_preview` (`DeletePreviewBoundary`, `DeletePreviewContribution`, `merge_delete_preview`), adds startup/runtime diagnostics for legacy `cv_get_related_objects` overrides and incompatible `Model.delete` signatures (`03-01`), and implements English/German partial-count and incomplete-preview notices (`03-02`).

### Strengths
- **Sound `RESTRICT` closure semantics (`06.3-DESIGN.md:48,59-61`):** Defers `RESTRICT` blocker decisions until the full supported `CASCADE` closure is computed, and refuses to let unknown boundaries or provider attestations clear a native `RESTRICT` candidate outside that closure.
- **Boundary-scoped provider validation (`T-06.3-04`, `T-06.3-05`):** Requires `DeletePreviewContribution.boundary` to match a package-emitted `DeletePreviewBoundary` from the current call, validates `isinstance(obj, Model)`, saved PKs, and `obj._state.db == using`, and runs `cv_filter_related_objects` *after* `merge_delete_preview` so contributed objects cannot bypass core or Guardian permission projection.
- **Immediate override diagnostics (`D-05`, `D-06`):** Detects legacy `cv_get_related_objects` overrides by method identity without invoking them, emitting both a system check Error and runtime `ImproperlyConfigured`.

### Concerns
- **[HIGH] Reverse relations on multi-table parents in `get_candidate_relations_to_delete(opts)`:**
  In Django (`django/db/models/deletion.py`), `get_candidate_relations_to_delete(opts)` inspects `opts.concrete_model._meta.get_fields(include_hidden=True)`, which includes reverse relations pointing to **parent models** in a multi-table inheritance hierarchy (`opts.parents`).
  1. When `inspect_deletion` traverses both `opts.parents` (`06.3-DESIGN.md:53`) and `get_candidate_relations_to_delete(opts)`, a reverse relation on a parent model will be seen on the child's `opts` *and* again when visiting the parent model unless deduplicated by relation/visited `(using, model, pk)`.
  2. When querying `_base_manager.using(using).filter(**{f"{field.name}__in": source_objs_or_pks})` for a reverse relation whose target (`field.remote_field.model`) is an ancestor model, if a custom `parent_link` does not share the child's PK value, filtering by the child's PK instead of the parent link's raw value (`getattr(child, parent_link.attname)`) would query the wrong key.
- **[MEDIUM] Detecting `cv_get_related_objects` overrides on both classes and instances:**
  In `tests/test1/test_delete.py:839`, tests sometimes use `monkeypatch.setattr(PublisherDeleteView, "cv_get_related_objects", ...)` (class attribute) or patch an instance. Checking `getattr(type(self), "cv_get_related_objects", None) is not DeleteView.cv_get_related_objects or "cv_get_related_objects" in self.__dict__` ensures both subclass overrides and instance-level patches are caught before invocation.
- **[MEDIUM] Partial summary wording in `related_objects.html` vs `related_summary_items`:**
  `06.3-DESIGN.md:89,94-95` states: *"incomplete summaries are labelled partial, including integer counts"* and *"Partial summary heading: 'Some related objects that will also be deleted (partial counts):'"*. Meanwhile, `src/crud_views/lib/views/delete.py:315` builds `context["related_summary_items"] = [f"{name}: {count}" for name, count in related.summary.items()]` and `src/crud_views/templates/crud_views/snippets/delete/related_objects.html:12` renders `{% cv_alert "warning" heading=_("The following related objects will also be deleted:") items=related_summary_items %}`. `03-02` should state explicitly whether only the `related_objects.html` alert `heading` changes when `delete_preview_incomplete` is `True` or whether `related_summary_items` strings also change (and ensure both msgids are in `src/crud_views/locale/de/LC_MESSAGES/django.po`).
- **[LOW] Check ID allocation for legacy `cv_get_related_objects` override:**
  In `src/crud_views/lib/views/delete.py:180-188` and `src/crud_views/lib/view/buttons.py:392`, view-level checks use `CheckExpression(context=cls, id="E25x", ...)` (which renders as `viewset.E25x`, where `E250`–`E255` and `E260`–`E262` are currently used). `03-01` should pick the next unused `E256` (or `E25x`) consistently across code and docs (`08-01`/`08-02`).

### Suggestions
- In `03-01`, specify how `inspect_deletion` handles parent-model reverse relations returned by `get_candidate_relations_to_delete(opts)` when also traversing `opts.parents` so parent relations are queried with the parent PK and never double-walked.
- In `03-02`, clarify that `related_summary` remains `dict[str, int]` and specify the exact `related_summary_items` and `heading` strings in English and German.

### Risk Assessment
- **Risk Level:** Medium. The graph traversal and provider validation have clear contracts in `06.3-DESIGN.md`, with multi-table parent traversal being the main edge case to get right.

---

## 06.3-04

### Summary
Completes `_DeleteCollector` and `execute_deletion` in `src/crud_views/lib/deletion.py` (`04-01`) and adds `transaction=True` commit, rollback, stale-preview race, and callback-provenance tests in `tests/test1/test_delete_provenance.py` and `tests/test1/test_delete.py` (`04-02`).

### Strengths
- **Fixes `CR-03` at the root cause (`DEL-03`):** Instead of inspecting tracebacks after `Collector.collect` has already caught and re-wrapped `ProtectedError` (`src/crud_views/lib/views/delete.py:97-126`), `_DeleteCollector` evaluates querysets outside any `ProtectedError` catch and only raises `_NativeDeleteBlocked` at explicit `handler is PROTECT` or outer `RESTRICT` reconciliation when `custom_callback_entered` is `False`.
- **Sticky `custom_callback_entered` provenance (`06.3-DESIGN.md:114-121`):** Prevents a request from returning a friendly 200/422 "blocked, nothing deleted" response if a custom `on_delete` or `SET` callback already executed (and potentially performed external I/O or unrolled writes under `cv_atomic=False`) before a subsequent native `PROTECT`/`RESTRICT` blocker was encountered.
- **Preserves `Collector.delete()` SQL executor:** Avoids hand-rolling SQL deletion, signal dispatching (`pre_delete`/`post_delete` with `origin`), fast-deletes, or PK clearing.

### Concerns
- **[HIGH] `_DeleteCollector` compatibility across Django 4.2, 5.2, and 6.0 internal `Collector` structures:**
  `_DeleteCollector` overrides `Collector.collect()` and delegates SQL execution to inherited `Collector.delete()` (`06.3-DESIGN.md:102-108`). Across Django 4.2, 5.2, and 6.0, `Collector.delete()` relies on specific internal attributes populated during `collect()`: `self.data`, `self.field_updates`, `self.restricted_objects`, `self.fast_deletes`, and `self.dependencies`.
  If `_DeleteCollector.collect()` directly manipulates `self.field_updates` or `self.restricted_objects` instead of calling `Collector`'s own helper methods (`self.add()`, `self.add_field_update()`, `self.add_dependency()`, `self.add_restricted_objects()`, `self.clear_restricted_objects_from_set()`, `self.clear_restricted_objects_from_queryset()`, `self.can_fast_delete()`, `self.related_objects()`, `self.get_del_batches()`), minor internal structure differences between Django 4.2 and 6.0 can break `Collector.delete()`.
- **[MEDIUM] Stale-preview test injection seam in `04-01` / `04-02`:**
  In `04-01` (`06.3-04-PLAN.md:83`), the plan states: *"Introduce stale protection using a real inspector/provider timing seam, not an empty preview substitution."*
  Because `DeleteView.post` (`src/crud_views/lib/views/delete.py:339-350`) runs:
  `context = self.get_context_data(**kwargs)` -> `self.cv_post_hook(context)` -> `if self.cv_form_is_valid(context):` -> `self.cv_form_valid_process(context)`,
  the cleanest real-request timing seam to insert a concurrent `Contract` or `Royalty` *after* real `get_context_data()` inspection completes and *before* `cv_form_valid_process()` runs is inside `cv_post_hook(context)` (or `form.clean()`). Using `cv_post_hook` in `test_delete_provenance.py` and `test_delete.py` tests the real `inspect_deletion` on `post()` (which sees no blocker at `get_context_data` time) followed by real `execute_deletion` (which catches the newly inserted blocker via `_NativeDeleteBlocked`), without any mock or preview substitution.
- **[LOW] Custom `Model.delete` signature inspection for `using` (`06.3-DESIGN.md:124-126`):**
  When checking `inspect.signature(target.delete)` before calling a custom `Model.delete(using=using)`, remember to accept both an explicit `using` keyword/positional-or-keyword parameter and `**kwargs` (`Parameter.VAR_KEYWORD`), since most custom `def delete(self, *args, **kwargs):` overrides in Django models and `PolymorphicModel.delete(self, using=None, keep_parents=False)` accept `using` via keyword or `**kwargs`.

### Suggestions
- In `04-01`, require `_DeleteCollector.collect` to delegate all state recording to `Collector`'s existing methods (`add`, `add_field_update`, `add_dependency`, `add_restricted_objects`, `clear_restricted_objects_from_set`, `clear_restricted_objects_from_queryset`, `can_fast_delete`, `related_objects`, `get_del_batches`).
- Use `cv_post_hook` as the standard stale-race injection point in `test_delete_provenance.py` and `test_delete.py`.

### Risk Assessment
- **Risk Level:** Medium-High. Adapting `Collector.collect` is the highest-complexity engineering task in Phase 06.3; relying on `Collector`'s own state-mutation helpers mitigates cross-version drift.

---

## 06.3-05

### Summary
Configures an independent second SQLite database (`shard`) in `tests/test1/conftest.py`, verifies single-alias pinning across inspection, deletion, `transaction.atomic`, and `transaction.on_commit` with colliding PKs and asymmetric protection (`05-01`), and scopes Guardian's `_PermittedPks` delete-preview label projection in `src/crud_views_guardian/lib/views.py` to the candidate object's database alias (`05-02`).

### Strengths
- **Reproduces and prevents `CR-04` (`DEL-04`):** Tests colliding `Publisher` PKs across `"default"` and `"shard"` with protection on only one alias in both directions, proving that `router.db_for_write(type(self.object), instance=self.object)` and `cv_get_delete_db_alias()` prevent a protected row on `"default"` from falsely blocking deletion of an unprotected row with the same PK on `"shard"`.
- **Identifies the multi-database cache collision in `_PermittedPks` (`src/crud_views_guardian/lib/views.py:59-95`):** Currently `self._cache` is keyed only by `model` (`views.py:77`) and queries `model._default_manager` (`line 81`) and `get_objects_for_user(..., klass=model)` (`line 92`) on the default database.

### Concerns
- **[HIGH] Cross-database PK grant leakage in `guardian.shortcuts.get_objects_for_user` when `UserObjectPermission` is not co-located on `using` (`05-02`):**
  Look closely at `src/crud_views_guardian/lib/views.py:87-94`:
  ```python
  ct = get_content_type(model)
  codename = f"view_{ct.model}"
  qs = get_objects_for_user(self.user, codename, klass=model, accept_global_perms=self.accept_global)
  self._cache[model] = set(qs.values_list("pk", flat=True))
  ```
  In `django-guardian`, `UserObjectPermission` and `GroupObjectPermission` store `(content_type_id, object_pk, user_id/group_id)` **without a database alias column**.
  If `05-02` simply changes `klass=model` to `klass=model._default_manager.using(using).all()` and keys `self._cache` by `(model, using)`, look at what happens when `UserObjectPermission` is read from `"default"` while `using == "shard"`:
  1. Suppose `user_guardian` holds a grant on `Contract(pk=1)` in `"default"`.
  2. When deleting a target on `"shard"` that is blocked by `Contract(pk=1, title="Shard Secret")` in `"shard"`, `get_objects_for_user(self.user, "view_contract", klass=Contract.objects.using("shard"))` queries `UserObjectPermission` (which resolves to `"default"` unless a router routes `guardian` to `"shard"`), retrieves `object_pk="1"`, and filters `Contract.objects.using("shard").filter(pk__in=["1"])`!
  3. As a result, a grant on `"default"` for PK 1 **reveals the label of PK 1 on `"shard"`**!
  4. Similarly, if `self.user._state.db` is `"default"` (e.g., `user.pk == 1`) and a custom router routes `UserObjectPermission` to `"shard"`, `get_objects_for_user` will query `UserObjectPermission` on `"shard"` with `user_id=1`—matching whatever user has `pk=1` on `"shard"`, violating `06.3-DESIGN.md:137` (*"do not treat an equal user PK as proof of actor identity"*).
  Therefore, in `_PermittedPks` (`src/crud_views_guardian/lib/views.py:74-95`):
  - `_PermittedPks` must check that the actor and permission tables resolve to the **same** database alias `using` as the candidate object (`self.user._state.db == using` and `router.db_for_read(UserObjectPermission, instance=self.user) == using` and `router.db_for_read(ContentType) == using`, using `ContentType.objects.db_manager(using)`).
  - Whenever the actor's database alias or Guardian's permission-table alias does not match `using`, `_PermittedPks` **must fail closed (`return set()`)** (including for global fallback and superusers if `self.user._state.db != using`), matching `06.3-DESIGN.md:138-141`!
- **[MEDIUM] `ContentType.objects` process-global cache across `default` and `shard` in `05-02`:**
  Django's `ContentTypeManager` caches `ContentType` instances per database alias in `ContentType.objects._cache`, and `guardian.ctypes.get_content_type(model)` calls `ContentType.objects.get_for_model(model)` (which uses `router.db_for_read(ContentType)`). In `test_delete_databases.py`, when a request-local router switches `ContentType` reads between `"default"` and `"shard"`, `ContentType.objects.clear_cache()` must be called around router changes (or `_PermittedPks` must validate `ct._state.db == using`) so a cached `ContentType` from `"default"` is never used to query permissions on `"shard"`.
- **[LOW] In-memory SQLite `shard` database configuration in `tests/test1/conftest.py:91-96`:**
  In `conftest.py:91-96`, adding `"shard": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}` creates a separate in-memory SQLite database. Note that in `pytest-django`, tests only set up tables on non-`default` databases when `@pytest.mark.django_db(databases=["default", "shard"])` is specified (or `databases="__all__"`), so existing single-DB tests remain fast while `test_delete_databases.py` uses `databases=["default", "shard"]`.

### Suggestions
- In `05-02`, explicitly require `_PermittedPks` to verify that `self.user._state.db == using` and that Guardian/auth/contenttype reads route to `using` (failing closed with `set()` when they do not), so a grant on `"default"` can never authorize a colliding PK on `"shard"` even without a custom Guardian router.
- Call `ContentType.objects.clear_cache()` in the multi-DB Guardian test fixture teardown/setup.

### Risk Assessment
- **Risk Level:** Medium-High (`05-02`'s Guardian multi-DB projection requires explicit alias-matching fail-closed logic to prevent `get_objects_for_user` from applying `"default"` `object_pk` rows to a `"shard"` queryset).

---

## 06.3-06

### Summary
Fixes `IN-02` and `IN-03` in `src/crud_views_guardian/lib/viewset.py` (`06-01`) by freezing `STRICT_HELPER_POLICY` with `MappingProxyType` and validating permission keys via `_resolve_permission_key(perm)` before inactive-user shortcuts or Guardian calls in `assign_perm`, `remove_perm`, and `get_objects_for_user`; then executes and records the bounded `GUA-01` / residual `AUTH-06` policy review in `06.3-GUARDIAN-REVIEW.md` (`06-02`).

### Strengths
- **Fixes `IN-02` without breaking `GuardianManageView` (`D-13`):** Wrapping `STRICT_HELPER_POLICY` (`src/crud_views_guardian/lib/viewset.py:11`) in `MappingProxyType` prevents accidental mutation from flipping `accept_global_perms` in `GuardianViewSet.get_objects_for_user` (`viewset.py:106`), while `GuardianManageView.get_context_data` (`src/crud_views_guardian/lib/views.py:296`) already copies it via `dict(STRICT_HELPER_POLICY)`.
- **Fixes `IN-03` across all three helpers and inactive users (`D-09`, `D-10`, `D-11`):** In `src/crud_views_guardian/lib/viewset.py:99-104`, `get_objects_for_user` currently returns `qs.none()` for an inactive user *before* looking up `self.permissions[perm]`, hiding typos like `"veiw"`. Validating `perm` first against `self.permissions` (`src/crud_views/lib/viewset/__init__.py:473-476`) and raising a descriptive `ValueError` with sorted valid keys fixes all three helpers consistently.
- **Disjoint file ownership in Wave 3:** `06.3-06` modifies `src/crud_views_guardian/lib/viewset.py` while `06.3-03` (also Wave 3) modifies `src/crud_views/lib/deletion.py` and `src/crud_views/lib/views/delete.py`, enabling safe parallel execution in Wave 3.

### Concerns
- **[MEDIUM] Unhashable or non-string `perm` arguments in `_resolve_permission_key(perm)`:**
  If a caller passes an unhashable value (such as `perm=["view"]` or `perm={}`) to `assign_perm`, `remove_perm`, or `get_objects_for_user`, a bare `if perm not in perms:` check will raise `TypeError: unhashable type` instead of the documented `ValueError`. Checking `if not isinstance(perm, str) or perm not in perms:` ensures all invalid key inputs raise the descriptive `ValueError`.
- **[LOW] Validation before default queryset construction in `get_objects_for_user`:**
  In `src/crud_views_guardian/lib/viewset.py:99-101`, `qs = qs if qs is not None else self.model.objects.all()` currently runs on line 99. `_resolve_permission_key(perm)` should be the very first statement in `get_objects_for_user` (before `qs` construction and before `_guardian_inactive_actor(user)`), matching `06.3-DESIGN.md:146`.

### Suggestions
- Guard `_resolve_permission_key(perm)` with `isinstance(perm, str)` before membership lookup in `self.permissions`, and place it at line 1 of `assign_perm`, `remove_perm`, and `get_objects_for_user`.

### Risk Assessment
- **Risk Level:** Low. Self-contained, well-specified changes with fast existing test suites (`test_guardian_policy.py` and `test_guardian_inactive.py`).

---

## 06.3-07

### Summary
Replays and extends core, Guardian, and native-template authorization tests with partial previews and safe-provider contributions (`07-01`), and adds real `transaction=True` polymorphic deletion and failure-propagation tests in `tests/test1/test_polymorphic.py` (`07-02`).

### Strengths
- **Closes the polymorphic deletion test gap (`DEL-03`, `DEL-05`):** Currently `tests/test1/test_polymorphic.py:162-192` only tests basic `Car` deletion and HTTP `DELETE` 405 rejection. `07-02` tests real `PolymorphicModel.delete(using=using)` execution, child `Car` and parent `Vehicle` row removal, signal origin, `DeletePreviewBoundary(kind="model_delete")` partial-preview status, and exception propagation under both `cv_atomic=True` and `cv_atomic=False`.
- **Verifies custom template overrides (`AUTH-03`, `AUTH-07`):** Extends `tests/test1/test_authorization_templates.py` (`lines 590-648`) to verify that `crud_views/tags/alert.html` overrides receive only permitted labels alongside the new incomplete-preview notice.

### Concerns
- **[HIGH] Broken file reference in `07-02` `<read_first>`: `@src/crud_views_polymorphic/lib/views.py` does not exist:**
  `06.3-07-PLAN.md:77` instructs the executor to read `@src/crud_views_polymorphic/lib/views.py`. That path does not exist in the repository; the polymorphic delete view is defined in `src/crud_views_polymorphic/lib/delete.py:1-10` (`PolymorphicDeleteView` and `PolymorphicDeleteViewPermissionRequired`) and re-exported in `src/crud_views_polymorphic/lib/__init__.py:7`.
- **[MEDIUM] Multi-table parent `Vehicle` handling when inspecting `Car` with `cv_show_related_objects=True` in `07-02`:**
  In `tests/test1/app/models.py:168-180`, `Car` inherits from `Vehicle(PolymorphicModel)` via multi-table inheritance (`vehicle_ptr`), and `Vehicle` has `polymorphic_ctype = ForeignKey(ContentType, on_delete=CASCADE)`. When `inspect_deletion` runs on `car_sedan`:
  - `Car.delete` is `PolymorphicModel.delete` (not `Model.delete`), which emits a `DeletePreviewBoundary(kind="model_delete", model=Car, field_name=None, using=using, source_pks=(car_sedan.pk,))`.
  - Meanwhile, `Car._meta.parents` contains `Vehicle`. `07-02` and `03-01` must agree on whether `inspect_deletion` walks `Car._meta.parents` into `Vehicle` (and whether `Vehicle` appears in `related_summary` or is excluded as a parent pointer of `Car`) so `07-02`'s assertions on `Car` preview summary and provider coverage are deterministic.
- **[LOW] Existing alert-count assertion in `tests/test1/test_authorization_templates.py:615`:**
  Line 615 asserts `assert content.count("<strong>MX-ALERT ") == 1` for a complete-preview `Publisher` blocked by `Contract`. When `07-01` adds partial-preview + blocked-deletion cases in `test_authorization_templates.py`, both the `warning` incomplete-preview alert and the `error` blocked-deletion alert will render through `crud_views/tags/alert.html`, producing `content.count("<strong>MX-ALERT ") == 2`. Keep the existing complete-preview test at `1` and assert `2` in the new partial+blocked test.

### Suggestions
- Fix `@src/crud_views_polymorphic/lib/views.py` in `06.3-07-PLAN.md:77` to `@src/crud_views_polymorphic/lib/delete.py`.
- Clarify the expected `related_summary` for `Car` (with `Vehicle` parent table) in `07-02`.

### Risk Assessment
- **Risk Level:** Low-Medium. Fixing the nonexistent `<read_first>` path and clarifying `Car`/`Vehicle` summary expectations avoids execution hiccups.

---

## 06.3-08

### Summary
Updates `docs/reference/delete_view.md`, `docs/reference/request_lifecycle.md`, `docs/reference/guardian.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`, and adds `tests/test1/test_delete_migration_docs.py` to extract and execute the published Python and Django template migration recipes (`08-01`, `08-02`).

### Strengths
- **Executable documentation recipes (`D-08`, `DEL-06`):** Follows the AST/fence extraction pattern in `tests/test1/test_form_button_docs.py:38-50,180-194` to execute the actual code blocks from `docs/migrating-1.0.md` and `docs/reference/delete_view.md` against real models, requests, and `locmem` template loaders rather than duplicating test-only fixtures.
- **Paired `### Breaking` and migration anchors (`CLAUDE.md:105`):** Ensures every `### Breaking` entry in `CHANGELOG.md` has a verified anchor and worked replacement in `docs/migrating-1.0.md`.

### Concerns
- **[MEDIUM] In-place replacement of Phase 6.2 `NestedObjects` and traceback-classifier prose in `CHANGELOG.md` and `docs/migrating-1.0.md`:**
  In the current repository, `docs/migrating-1.0.md:400-492` (`#delete-previews-and-protected-objects` and `#blocked-deletions`), `docs/reference/delete_view.md:193-204,313-328`, and `CHANGELOG.md:172-191` contain extensive Phase 6.2 prose describing:
  - `NestedObjects` running on every GET/POST (`delete_view.md:196`, `migrating-1.0.md:489`),
  - overriding `cv_get_related_objects()` for previews-off blocked state (`delete_view.md:200`, `migrating-1.0.md:487`),
  - `_cv_has_native_collection_graph` and `Model.delete` / `Collector.collect` traceback frame checks (`delete_view.md:313-319`, `migrating-1.0.md:473-485`), and
  - `{% if related_summary or has_protected_objects %}` without `delete_preview_incomplete` (`migrating-1.0.md:414,442`).
  `08-01` and `08-02` must edit those existing sections in `docs/migrating-1.0.md` and `CHANGELOG.md` in place so a 0.29→1.0 upgrader is not given contradictory instructions in the same document.
- **[LOW] System check table in `docs/migrating-1.0.md:34-50` ("Step zero: run the checks"):**
  `docs/migrating-1.0.md:34-50` lists system check codes and runtime exceptions encountered during upgrade. `08-01` should add the new system check ID for legacy `cv_get_related_objects` overrides and its runtime `ImproperlyConfigured` error to that summary list as well as to the delete migration section.

### Suggestions
- In `08-01` and `08-02`, add an explicit assertion in `test_delete_migration_docs.py` that obsolete terms (`NestedObjects`, `_cv_has_native_collection_graph`, "traceback") no longer appear as active contract claims in `docs/reference/delete_view.md` or `docs/migrating-1.0.md`.

### Risk Assessment
- **Risk Level:** Low-Medium. Straightforward documentation and doc-test execution once Waves 2–6 settle the runtime behavior.

---

## 06.3-09

### Summary
Provisions the verified Django 5.2 nox environment, runs the focused and full test suites across Django 4.2, 5.2, and 6.0 alongside `npm test`, `mkdocs build --strict`, and `ruff`, records exact runtime provenance in `06.3-MATRIX.md` (`09-01`), and reconciles `06.2-ACCEPTANCE.md` / `06.3-ACCEPTANCE.md` / `06.3-VALIDATION.md` (`09-02`).

### Strengths
- **Full three-series verification (`DEL-06`, `D-15`):** Covers Django 4.2, 5.2, and 6.0 without conflating the main `.venv` (Django 6.1.2) with supported-series evidence.
- **Rigorous acceptance reconciliation (`D-16`):** Preserves the distinction between retained Phase 6.2 evidence, newly evidenced Phase 6.3 fixes (`CR-02`–`CR-04`, `IN-02`–`IN-03`, `GUA-01`), and out-of-scope boundaries (`A19`, `A25`).

### Concerns
- **[HIGH] `C0901` verification command runs full `tests/test1` serially on Django 4.2 and 6.0 without `-n`, risking a >15-minute command timeout:**
  Look at `06.3-09-PLAN.md:79` (`C0901`, also in `06.3-VALIDATION.md:156`):
  ```bash
  for dcv_django in 4-2 6-0; do PYTHONPATH="$PWD/src:$PWD" .nox/crispy_floor-3-12-django-${dcv_django}/bin/python -m pytest tests/test1 --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline -q -p no:cacheprovider || exit $?; done && .venv/bin/python -m nox -r --no-install -s "tests-3.12(django='5.2')" && npm test && .venv/bin/mkdocs build --strict && .venv/bin/ruff check src tests && .venv/bin/ruff format --check src tests
  ```
  In `06.2-ACCEPTANCE.md:76-77,125-128`, running full `tests/test1` (6,451+ tests) serially took **587.24s (~9.8 min)** on Django 6.0 and **301.48s (~5.0 min)** on Django 4.2, whereas with `-n 8` (`pytest-xdist` is installed in both environments, see `pyproject.toml:77` and `noxfile.py:19,106`) it took **64.56s**! Running both serial full suites plus `nox -s "tests-3.12(django='5.2')"` in a single chained shell command will take ~16–20 minutes and exceed the default 120s Bash tool timeout unless `-n auto` / `-n 8` (and a larger timeout) is used.
- **[MEDIUM] `nox -r --no-install -s "tests-3.12(django='5.2')"` in `C0901` requires a prior fresh install of the current working tree:**
  In `noxfile.py:13-14` and `pyproject.toml:143-145`, `nox` installs `django-crud-views` as a wheel into `.nox/tests-3-12-django-5-2/lib/python3.12/site-packages/` rather than using an editable install or `PYTHONPATH="$PWD/src:$PWD"`. In `09-01`, the `<action>` runs `.venv/bin/python -m nox -s "tests-3.12(django='5.2')"` (which installs the current source tree), and then `<verify>` runs `.venv/bin/python -m nox -r --no-install -s "tests-3.12(django='5.2')"`. If any file in `src/` is touched between the initial provisioning run and `C0901`, `--no-install` will test stale code in `site-packages/`!

### Suggestions
- Add `-n auto` (or `-n 8`) to the `4-2` and `6-0` full-suite `pytest` invocations in `C0901` (`06.3-09-PLAN.md:79` and `06.3-VALIDATION.md:156`), matching `noxfile.py:19,106`.
- In `09-01`, verify `crud_views.__file__` (or pass `PYTHONPATH="$PWD/src:$PWD"` when invoking `.nox/tests-3-12-django-5-2/bin/python -m pytest`) so the 5.2 session is guaranteed to execute against the current `src/` tree.

### Risk Assessment
- **Risk Level:** Medium (operational timeout and `site-packages` vs `src/` import path in `C0901`).

---

## Cross-Plan Conclusions

### Architecture & Design Fitness
The integrated architecture in `06.3-DESIGN.md` is well-grounded in the actual Django and repository source code:
1. **`CR-02` (`DEL-02`):** Replacing `NestedObjects.collect` in `DeleteView` with a metadata-only `_DeleteInspector` (`inspect_deletion`) and a boundary-scoped `cv_get_delete_preview` hook is the right design. Because Django's `SET(...)` and `SET_DEFAULT` execute their factories inside `Collector.collect` *before* `Collector.add_field_update`, subclassing `Collector` for preview cannot prevent callback execution.
2. **`CR-03` (`DEL-03`):** Replacing `_cv_has_native_collection_graph` and `_cv_is_target_collection_protection` (`src/crud_views/lib/views/delete.py:43-126`) with `_DeleteCollector` and sticky `custom_callback_entered` provenance directly resolves the converter counterexample where Django's `Collector.collect` caught and re-wrapped a nested converter's `ProtectedError`.
3. **`CR-04` (`DEL-04`):** Pinning `cv_get_delete_db_alias()` once per request using `router.db_for_write(type(self.object), instance=self.object)` and threading it through `inspect_deletion`, `execute_deletion`, `cv_get_atomic`, `transaction.on_commit`, and Guardian's `_PermittedPks` closes the multi-database split-brain defect.
4. **`GUA-01` (`IN-02`, `IN-03`, residual `AUTH-06`):** Wrapping `STRICT_HELPER_POLICY` in `MappingProxyType` and validating permission keys via `_resolve_permission_key` before `_guardian_inactive_actor` in `src/crud_views_guardian/lib/viewset.py:77-108` is minimal, accurate, and preserves Phase 6.2's per-view fallback and strict helper semantics.

### Top Cross-Plan Issues to Resolve Before Execution
1. **[HIGH — Wave 2 / Wave 4 ordering in `tests/test1/test_delete.py` (`06.3-02` vs `06.3-04`)]:**
   `C0202` runs `tests/test1/test_delete.py` in Wave 2, but `test_delete.py:789-1469` currently imports `_cv_has_native_collection_graph` / `_cv_is_target_collection_protection` and monkeypatches `cv_get_related_objects` in `_delete_probe` and `test_delete_native_target_backstop_keeps_storage` to bypass precheck protection. `02-02` must update those tests in `test_delete.py` (using `cv_post_hook` to inject stale-race protectors after `get_context_data`) rather than leaving them broken until `06.3-04`.
2. **[HIGH — Guardian multi-DB cross-alias PK grant leak in `_PermittedPks` (`06.3-05`)]:**
   In `src/crud_views_guardian/lib/views.py:87-94`, passing `klass=model._default_manager.using(using)` to `guardian.shortcuts.get_objects_for_user` is not sufficient by itself: because `UserObjectPermission.object_pk` has no database column, Guardian will query `UserObjectPermission` on `"default"` and filter the `"shard"` queryset by those PKs unless `_PermittedPks` verifies that `self.user._state.db == using` and Guardian/auth/contenttype reads route to `using` (failing closed with `set()` otherwise).
3. **[HIGH — Non-existent `<read_first>` path in `06.3-07`]:**
   Replace `@src/crud_views_polymorphic/lib/views.py` in `06.3-07-PLAN.md:77` with `@src/crud_views_polymorphic/lib/delete.py`.
4. **[HIGH — Serial full-suite runtime in `C0901` (`06.3-09`, `06.3-VALIDATION.md`)]:**
   Add `-n auto` (or `-n 8`) to the `4-2` and `6-0` full-suite `pytest` loops in `C0901` so the verification command completes within tool timeout limits.
