I'll review all six plans against the current source and the prior closure ledger, starting with the call sites those findings depend on.
The URL, delete, and Guardian call sites match the prior findings. Next I’ll trace button, create, and browser consumers the revised plans claim to own.
Intel has no symbol index, so declarations are UNCHECKABLE from that authority. The conclusions below rest on live source reads.

## 06.10-01

Summary: Wave 1 builds one metadata-aware resolver and public `get_parent_pks`/`get_url`, then proves mixed-parent rendering without touching request scope.

Strengths: The matrix matches the current overwrite. `cv_get_router_and_args` copies page kwargs into the reverse dict (`src/crud_views/lib/view/base.py:598`) before `cv_get_url` reverses (`base.py:615`). Plan text separates page kwargs from explicit kwargs and ignores stale page ancestry for object targets (`.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-PLAN.md` Resolution contract). `ParentViewSet.get_attribute`/`get_pk_name` are the declared metadata (`src/crud_views/lib/viewset/parentviewset.py:56`). The isolated `NestedUrl*` family does not add a Publisher reverse edge; existing `Genre.publishers` already points at Publisher (`tests/test1/app/models.py:59`). Replaying `tests/test1/test_delete_inspection.py` is the right topology check because inspection walks `get_candidate_relations_to_delete` (`src/crud_views/lib/deletion.py:118`).

Concerns:
- MEDIUM: Object-assertion retention names the wrong type. `cv_get_cls_assert_object` calls `cv_raise` with no exception argument (`base.py:555`). `cv_raise` defaults to `ViewSetError`, not `CrudViewError` (`src/crud_views/lib/exceptions.py:27`). The plan says retain `CrudViewError` (01-PLAN.md Compatibility boundary). An executor can either fail the new test or change the raised type.

Suggestions: Pin `ViewSetError` for that assertion. Keep `ViewSetKeyFoundError` only for `get_view_class` (`src/crud_views/lib/viewset/__init__.py:342`).

Risk Assessment: Low if the exception pin is corrected. Precedence, query bounds, and fixture isolation are executable.

## 06.10-02

Summary: Wave 2 wires view builders and a call-scoped carrier so collection page A and object B stay distinct without changing hook signatures.

Strengths: Current builders are the right seams. `ContextButton.get_context` builds the URL before `cv_has_access` (`src/crud_views/lib/view/buttons.py:103`). `ParentContextButton` already takes ancestor kwargs from the page (`buttons.py:159`) and checks `cv_get_parent_object` (`buttons.py:179`). `SiblingContextButton` passes `obj=None` (`buttons.py:301`). `cv_get_child_url` crashes on a root ViewSet via `viewset.parent.name` (`base.py:990`). The plan guards that with `ParentViewSetError` and keeps sibling/filter paths out of the destination frame (02-PLAN.md Scope roles). Carrier misses are split into unpublished-matching versus absent, with database-free concurrency tests.

Concerns:
- MEDIUM: Repeats the `CrudViewError` pin for missing/falsey view objects (02-PLAN.md Scope roles). Same source mechanism as plan 01.

Suggestions: State that `LinkDetailColumnMixin` still depends on `ViewSetKeyFoundError` being raised inside `cv_get_url`, because `@ignore_exception(ViewSetKeyFoundError)` is the fallback (`src/crud_views/lib/table/columns.py:48`).

Risk Assessment: Low after the exception correction. The carrier is justified: a cooperative `cv_has_access(user, row_B)` cannot otherwise see page A.

## 06.10-03

Summary: Wave 3 makes missing declarations fail closed and applies Guardian’s direct-parent rule to the selected destination, including create and certified availability.

Strengths: `GuardianCreateViewPermissionRequired` defines its own `cv_has_access` (`src/crud_views_guardian/lib/views.py:344`), so a new parent-mixin method would not run for create. The plan edits that method and the private rendering adapter instead of relying on MRO (03-PLAN.md Nested create). Top-level create currently falls through `GuardianParentPermissionMixin.has_permission` (`src/crud_views_guardian/lib/mixins.py:307`) into the core assert (`base.py:1062`). Dispatch already denies anonymous and inactive users before `super().dispatch` (`mixins.py:313`). The plan keeps that prelude and names the create declaration guard. Certified availability reads `_cv_cancel_parent_object` once, returns false when it is missing, and skips a second parent check only when `parent_gate_owner=certified-adapter` (03-PLAN.md Certified availability). Private-to-public forwarding avoids recursion: callers stay on `_guardian_user_has_parent_perm` (`mixins.py:348`), and the public default must not call it back.

Concerns: None.

Suggestions: Document that a public override must not call the private helper.

Risk Assessment: Low. Opposite-grant, create A/B, and non-delegating certified-parent tests are concrete.

## 06.10-04

Summary: Wave 4, after plan 03, reuses optional `get_url` for multilevel delete candidates and keeps certification independent.

Strengths: Stock assembly is one level and swallows `NoReverseMatch` (`src/crud_views/lib/views/delete.py:192`). Certification is a later exact-candidate check (`delete.py:212`), and the parent lambda is installed only after alias checks (`delete.py:356`). The plan keeps that order, requires the same parent instance for cooperative and non-delegating hooks, and blocks on plan 03 rather than deferring to browser evidence (04-PLAN.md Ordered ownership). `database_routes` exists (`tests/test1/conftest.py:137`). Query bounds are explicit today (`tests/test1/test_delete_databases.py:210`); the plan replaces them after measurement.

Concerns: None.

Suggestions: Spies should record the alias actually queried. The test router ignores instance hints and follows its ContextVar (`conftest.py:148`).

Risk Assessment: Low. Fail-closed text for a missing certified parent is specified, not implied.

## 06.10-05

Summary: Wave 5 publishes executable migration and a Phase 7 handoff without classifying stability tiers.

Strengths: `docs/development/stability.md:19` defines the public list, and `stability.md:83` lists Guardian classes but not the new helper. The plan adds a marked handoff subsection, repeats it in the summary, and leaves tier assignment to Phase 7 (05-PLAN.md Artifacts). Breadcrumb ancestors are built from URL kwargs (`src/crud_views/lib/breadcrumb.py:232`), so documenting preserved ancestor scope matches the code that plan 02 replays.

Concerns: None.

Suggestions: If the object-assertion exception is documented, name `ViewSetError`, not `CrudViewError`.

Risk Assessment: Low. Recipe execution is fenced and existing protected-delete markers stay intact.

## 06.10-06

Summary: Wave 6 captures stock/custom browser evidence only after the serialized Guardian/delete work, then revalidates hashes after the gates.

Strengths: Runner and server manifests currently disagree with untracked files: both use `git ls-files` without `--others` (`tests/browser/protected-delete.cjs:36`, `tests/browser/protected_delete_server.py:70`) and compare them at startup (`protected-delete.cjs:133`). The plan requires one cached-plus-untracked manifest, explicit `resolution.py`/`link_context.py` presence, and identical tooltip recipe keys. `buttons.md` fences are adjacent (`docs/reference/buttons.md:783`). Old `all` still requires `screenshots/protected-*-modal.png` (`protected-delete.cjs:74`). Final `validateEvidence` runs after lint/docs (`06-PLAN.md` task 06-03). Browser navigation still rejects status 403 (`protected-delete.cjs:53`); the plan keeps that and assigns the unresolved-parent 403 to plan 03.

Concerns: None.

Suggestions: Keep new action IDs out of the delete loop at `protected-delete.cjs:184`. That loop treats `-click`/`-modal-` as protected-delete DOM.

Risk Assessment: Low. Identity, schema, and recapture rules are executable. Browser runtime remains an execution preflight, not a pass.

## Cross-plan assessment

The six plans are serial waves and 16 tasks, matching the dependency frontmatter. Plan 03 owns the certified-parent gate; plan 04 is the real-delete integration check; plan 06 cannot record acceptance over a failed earlier seam. Object versus collection precedence, strict ordinary rendering, and optional delete text are consistent across 01, 02, 04, and 05. Create access is not left to MRO: 02 owns core state, 03 owns Guardian’s non-delegating create method. No new product prohibition or parallel-wave contradiction showed up.

The one substantive new defect is the shared `CrudViewError` pin in plans 01 and 02. Everything else from cycle 1 has an executable mitigation or an explicit, source-compatible disposition.

## Closure ledger

| ID | Status | Evidence |
|---|---|---|
| C1-H1 | CLOSED | 03-PLAN.md Certified availability: one read, missing parent returns false, `certified-adapter` skips a second parent check, non-delegating `cv_has_access` cannot bypass the earlier gate. 04 depends on 03 and tests the lambda at `delete.py:368`. Waves are serial. |
| C1-H2 | CLOSED | 01-PLAN.md creates `NestedUrlRoot` and forbids a new Publisher relation. 01-02 replays `test_delete_inspection.py`. Genre rows use an existing M2M (`models.py:59`). |
| C1-H3 | CLOSED | 02-PLAN.md Scope roles: sibling stays `obj=None`; middle-tier parent collections bind remaining page ancestors. 03-02 tests opposite grants. 05-02 documents breadcrumb ancestors, which still come from URL kwargs (`breadcrumb.py:232`). |
| C1-H4 | CLOSED | Create’s own `cv_has_access` is at `views.py:344`. 02-02 selects collection parent A for core state. 03-02 edits that create method, the rendering adapter, and the list correction. |
| C1-H5 | CLOSED | 03-01 names `GuardianParentPermissionMixin.has_permission` before the core assert (`mixins.py:307`, `base.py:1062`). Actor prelude stays in `dispatch` (`mixins.py:313`). GET/POST matrix covers active, inactive, anonymous, and superuser. |
| C1-H6 | CLOSED | 06-PLAN.md Browser identity: identical `--cached --others --exclude-standard` manifests, required new module paths, shared tooltip recipe keys, startup equality. |
| C1-M01 | CLOSED | 01 and 02 keep ordinary null/unscoped rendering as strict `ValueError`. Optional `strict=False` is delete-only. |
| C1-M02 | PARTIAL | Unknown keys stay `ViewSetKeyFoundError` at `viewset/__init__.py:342`, and public `get_url` is the only `NoReverseMatch` translation. The object assertion is mis-pinned: source raises `ViewSetError` (`base.py:555`, `exceptions.py:27`). Change the plan text to `ViewSetError` before execution. |
| C1-M03 | CLOSED | 01 names M2M zero/one/two, self-FK, and Resource subclass fixtures. 03/04/06 name isolated Guardian and browser routes. |
| C1-M04 | CLOSED | 01-02 uses the registered model’s PK metadata and a subclass with distinct base and child IDs. |
| C1-M05 | CLOSED | 02-02 names `LinkDetailColumnMixin`, `LinkChildColumn`, `RedirectChildView`, and `FilterContextButton`. 03-02 names the URL-free access filter at `templatetags/crud_views.py:607`. |
| C1-M06 | CLOSED | 02-02 replaces the broad `ObjectDoesNotExist` swallow in `create.py:45` and requires the original exception to escape. |
| C1-M07 | CLOSED | 02-01 guards `parent is None` before `.name` (`base.py:990`) and raises `ParentViewSetError`. |
| C1-M08 | CLOSED | 02-02 separates matching-unpublished page scope from absent-scope misses and uses sentinel concurrency tests. |
| C1-M09 | CLOSED | 03-02 tests only the direct destination parent, including an unavailable older ancestor. Request dispatch remains one parent (`mixins.py:370`). |
| C1-M10 | CLOSED | 03-01 covers sibling/no-object, Resource maps, actor-before-configuration order, and cross-ViewSet empty-map retry. |
| C1-M11 | CLOSED | 05-01/02 document superuser denial, implicit page-A-plus-obj-B versus explicit conflict, and preserved ancestor navigation. |
| C1-M12 | CLOSED | 04-02 replaces the N=1/4/8 counters in `test_delete_databases.py:210` and keeps the excess-work control. |
| C1-M13 | CLOSED | 05-03 adds a handoff subsection for the class and method, copies it to the summary, and does not edit the current Public API list (`stability.md:19`). |
| C1-M14 | CLOSED | 06-03 revalidates persisted evidence after the last gate and recaptures `nested-all` if hashes move. |
| C1-M15 | CLOSED | 403 stays in plan 03’s client tests. Browser schema still requires successful navigation (`protected-delete.cjs:53`). |
| C1-M16 | CLOSED | 06-01 keeps `recipes(source, expected)`, LF bodies, old `all` screenshots, and adds family-specific nested screenshots. |
| C1-M17 | CLOSED | 06-01 limits delete patches to original source/detail routes. Detail keeps `x-protected-detail-modal-capable`, which old navigation asserts (`protected-delete.cjs:223`). |
| C1-M18 | CLOSED | 04-02 adds an intermediate ancestor mismatch under `database_routes` and requires alias/identity spies. |
| C1-M19 | CLOSED | 03-PLAN.md: private entry forwards to public; public default does not call private; both override forms are tested. |
