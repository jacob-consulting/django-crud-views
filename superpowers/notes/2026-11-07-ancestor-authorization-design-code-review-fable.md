# Code review: ancestor authorization spec against the codebase

Date: 2026-11-07. Reviewer: Claude (Fable 5.1), extra-high-effort recall review. Target:
[2026-11-07-ancestor-authorization-design.md](2026-11-07-ancestor-authorization-design.md) (spec, HEAD `4b256bdb`),
read against the current `src/`, `tests/` and `docs/`. The
[discussion record](2026-11-07-guardian-child-permissions-discussion.md) was consulted for rationale only.

This review does not reopen approved product decisions. It lists places where the approved text conflicts with
code that exists today, under-specifies something the code makes unavoidable, or leaves a migration gap. Per the
spec's own GSD rule ("If new code evidence creates a genuine conflict, identify the affected decision and the
evidence; ask only about that conflict"), each finding names the decision ID it touches. Nothing here was run;
all evidence is source inspection. No code, plan or phase artifact was created.

Line numbers refer to the reviewed spec revision unless a source path is given. The original findings below
are preserved; subsequent decisions and design amendments are recorded separately here.

## Maintainer dispositions

| Finding | Status | Agreed resolution |
| --- | --- | --- |
| 1 — nested Resource leaves | **Accepted, 2026-11-07** | Preserve Resource leaves beneath one or more ORM ViewSets in both cascade modes. Resources must remain leaves and cannot parent an ORM ViewSet or another Resource. Shared traversal validates and authorizes the ORM ancestry; the existing Resource loading/scoping contract remains responsible for leaf membership. Recorded as D-39, superseding D-29's blanket exclusion, in the design. |
| 2 — Guardian child beneath a core parent | **Accepted as a migration-documentation gap, 2026-11-07** | D-40 preserves D-06's provider defaults. Document the change from object-based to model-based parent checks, including possible access loss/gain. To retain object-based ancestor protection, migrate the parent to GuardianViewSet; C-02 still rejects provider="guardian" on core. Child-local checks stay independent. Add acceptance coverage for the default and migration path; no automatic compatibility translation or new mixed-composition warning. |
| 3 — child-view global fallback loses its parent-check role | **Accepted as a migration and diagnostics clarification, 2026-11-07** | D-41 retains separate ancestor and endpoint-local settings, with no default/override relationship. Document that the child-view flag no longer affects ancestors; explicitly configure fallback on a Guardian ancestor when intended, accounting for its shared scope across descendant endpoints. Update manage diagnostics and acceptance coverage to prove independence in both directions. |
| 4 — ancestor enforcement order | **Accepted as an integration-order clarification, 2026-11-07** | D-42 makes B-03 ordering explicit across supported shipped compositions. A check only in CrudView.dispatch() is insufficient. Keep one shared authorization implementation, allowing small explicit integration bridges; leave the precise hook to implementation planning. Preserve local checks and supported denial responses, and require tests proving ancestor denial prevents downstream processing. |
| 5 — all-none ancestry reveals existence before local actor denial | **Accepted, 2026-11-07** | D-43 preserves existing endpoint early anonymous/inactive denials before ancestor lookup even for all-none ancestry. Refine B-01/B-03 and D-42 while keeping static validation first and child-object/state/form/write processing after ancestry. Preserve supported denial responses and otherwise-public backend/manage behavior; do not infer a universal login requirement from PermissionRequiredMixin. |
| 6 — rejected ViewSets leak into the registry | **Accepted, 2026-11-07** | D-44 requires new constructor-checkable policy constraints to be validated before ViewSet registration and automatic manage-view creation. Rejection must leave no registration behind and allow a corrected declaration to reuse the name. Completed-registry checks remain deferred. Prefer early validation over rollback machinery; require clean-rejection and successful-retry tests. |
| 7 — nested manage acquires ancestor checks | **Accepted as a manage-access clarification, 2026-11-07** | D-45 retains Read classification and normal ancestor authorization/relationship validation for nested manage pages. Preserve existing manage-specific access rules as an additional independent gate; settings/group membership do not bypass ancestry. Document/test the nested access change and preserve top-level behavior. No exemption is introduced. |
| 8 — built-in child redirect lacks a family | **Accepted, 2026-11-07** | D-46 classifies RedirectChildView as Read, with normal ancestor checks and no required action entry merely for using the built-in family. Preserve object lookup/local checks, retain explicit action overrides, and require the destination to enforce its own ancestor/local permissions. Arbitrary redirects and custom actions receive no inferred classification. |
| 9 — ineffective request settings without a parent | **Accepted, 2026-11-07** | D-47 rejects non-None cascade/read/write and nonempty actions on a ViewSet without a parent, before registration under D-44. None/empty defaults remain valid; provider/fallback retain their existing scope and validation. Global defaults do not trigger rejection. Descendant request requirements belong on the requested descendant ViewSet. |
| 10 — action keys versus list/card alias | **Accepted, 2026-11-07** | D-48 requires exact registered keys for ancestor action validation and override resolution. An unregistered list key is invalid even when navigation resolves it to card. Separate list/card endpoints keep separate overrides; a card view actually registered as list accepts that key. Preserve navigation aliases, built-in Read defaults, and completed-registration validation timing. |
| 11 — nested custom action migration omitted | **Accepted as a migration-documentation gap, 2026-11-07** | D-49 preserves the explicit action-entry requirement and documents it as a breaking upgrade for core and Guardian applications in both cascade modes. Add a migration-table row and require the eventual feature's Breaking changelog and docs/migrating-1.0.md updates to explain declarations, failure behavior, and built-in/top-level exceptions. No permission-policy change. |
| 12 — ParentViewSet example import | **Accepted as an example-only cleanup, 2026-11-07** | D-50 imports ParentViewSet alongside the other ViewSet configuration types from crud_views.lib.viewset, where it is already exported. No permission or API behavior change. |

Finding 1's resolution preserves existing nested Resource support rather than retiring it. The design ledger,
P-03 table, scope, request behavior, acceptance evidence, and technical addendum have been updated accordingly.
There is no new generic Resource membership validator. Top-level Resource behavior remains unchanged.
This approval covers the documentation amendment, not planning, implementation, or a commit.

Finding 2's resolution adds an explicit migration row, before/after permission table, and acceptance criteria
to the design. The original suggestion to use provider="guardian" on a core parent is not adopted because it
conflicts with C-02; the supported migration uses GuardianViewSet. The suggested mixed-composition warning is
also not adopted. The provider defaults themselves are unchanged. Implementation and test code remain deferred.

Finding 3's resolution clarifies that Book's ancestor policy applies when Book is an ancestor, while the Book
view's flag applies to its own local permission check where applicable. Neither setting supplies a default for
or overrides the other. The design's migration row, explanation, diagnostic requirements, and acceptance
criteria were updated; the original finding below is preserved. No implementation or commit is authorized
by this approval.

Finding 4's resolution clarifies the existing order rather than changing permission policy. Multiple small
bridges into the same implementation are not automatically multiple authorization mechanisms. No specific
`as_view()`/`setup()` solution is selected; Django ignores setup's return value, so a redirect cannot simply
be returned from there. The design's request contract, MRO addendum, and acceptance criteria were updated.
The original finding remains unchanged below. Implementation and commits remain separately authorized work.

Finding 5's approved resolution preserves early actor denials rather than running the complete local
permission/object/state pipeline ahead of ancestry. It does not assume every permission-required composition
forbids anonymous access: supported backend and manage behavior must remain intact. The design's actor and
ordering tables, examples, and acceptance criteria were reconciled with D-43, including its refinement of
finding 4. The maintainer explicitly requested committing this documentation update; implementation remains
deferred. Original findings are retained below.

Finding 6's resolution specifies clean construction failure without moving completed-registry checks into
construction. The exact validator arrangement remains an implementation choice. An isolated review probe
confirmed that a rejecting after-validator placed after the current registration step leaves the rejected
ViewSet and its auto manage view registered, preventing a valid retry under the same name. This confirms the
ordering hazard, not a defect in the unimplemented policy API. The design's C-02 contract, technical addendum,
and acceptance criteria were updated. The maintainer requested a documentation commit; implementation remains
deferred and the original finding is preserved below.

Finding 7's resolution distinguishes the unchanged local manage gate from total access to a nested endpoint.
It retains the approved ancestor Read classification; the suggested exemption is not adopted. All-none chains
still require relationship validation and preserve D-43 actor rules, while top-level manage behavior remains
unchanged. The design's operation table, migration guidance, manage wording, and acceptance criteria were
updated. The maintainer requested a documentation commit; original findings remain unchanged below.

Finding 8's resolution adds the shipped RedirectChildView family to the finite Read classification. A successful
redirect does not grant access to the destination: that request applies its own operation and permission rules.
The design's operation table, acceptance criteria, and technical addendum were updated without generalizing
the rule to arbitrary redirects or custom actions. The maintainer requested a documentation commit;
implementation remains deferred and the original findings are preserved below.

Finding 9's resolution chooses a configuration error for ineffective non-default request declarations on a
ViewSet without a parent. The scope distinction remains explicit: provider/fallback describe the ViewSet as an
ancestor, while cascade/read/write/actions describe requests targeting it. Explicit None/empty defaults and
valid global settings remain accepted. The design's validation table, explanation, acceptance criteria, and
technical addendum were updated. The maintainer requested a documentation commit; implementation remains
deferred and the original findings are preserved below.

Finding 10's resolution keeps permission declarations tied to exact registered endpoints. Navigation fallback
continues to work, but does not create an action-policy alias or redirect one endpoint's override to another.
Card endpoints retain normal Read requirements without an override. The design's API/validation tables,
operation rules, acceptance criteria, and technical addendum were updated. The maintainer requested a
documentation commit; implementation remains deferred and the original findings are preserved below.

Finding 11's resolution identifies the existing custom endpoint declaration rule as a breaking migration
requirement beyond Guardian applications. Missing entries remain system-check errors and runtime configuration
failures; switching to nearest-only mode does not avoid them. The design now includes a migration-table row,
an explanation, and explicit release-documentation acceptance criteria. Actual changelog/migration-guide
edits accompany implementation. The maintainer requested a documentation commit; implementation remains
deferred and the original findings are preserved below.

Finding 12's resolution makes the C-01 example consistently import from the public ViewSet module. The
existing submodule import remains valid. The maintainer requested a documentation commit; no implementation
change is involved. All twelve findings now have approved dispositions, recorded as D-39–D-50 in the design.
The original review below remains unchanged; planning and implementation remain deferred.

## Summary

| # | Severity | Decision(s) | Finding |
| --- | --- | --- | --- |
| 1 | High | D-29 / P-03 | "Resource anywhere in a nested chain is a configuration error" removes the shipped, documented and tested nested Resource *leaf* |
| 2 | High | D-06, P-02 | Guardian child under a core parent silently flips from object grant to model permission; no migration row |
| 3 | High | D-18, P-02, B-05 | Child view `cv_guardian_accept_global_perms` silently loses its parent-check role; users lose access with no error |
| 4 | Medium-High | B-03, readability criteria | `CrudView.dispatch()` can never be the entry point: Django's permission dispatch *always* precedes it in every shipped `*PermissionRequired` composition |
| 5 | Medium | B-01, B-03 | All-none ancestry: relationship 404s run before endpoint authentication, creating an anonymous existence oracle that does not exist today |
| 6 | Medium | C-02, P-02 | ViewSet-dependent validation placed after `register()` leaks rejected ViewSets into `_REGISTRY` |
| 7 | Medium | B-02, B-05 | Nested auto-registered manage views acquire login + ancestor gates and parent 404s; spec also says the manage gate must not change |
| 8 | Medium | B-02, D-17 | Shipped `RedirectChildView` has no B-02 family; nested use becomes a configuration error for a package view |
| 9 | Low-Medium | C-02 (D-36) | "Reject ineffective configuration" does not cover cascade/read/write/actions declared on a ViewSet with no parent |
| 10 | Low | C-02 | `actions` key validation vs the existing `list` to `card` alias is unspecified |
| 11 | Low | D-17, P-02 | Migration table omits that every nested custom action now needs an `actions` entry (startup-breaking) |
| 12 | Low | C-01 example | Example imports `ParentViewSet` from a submodule although `crud_views.lib.viewset` already exports it |

## Findings

### 1. High: D-29/P-03 regresses the shipped nested Resource leaf

Spec lines 57, 93, 231, 234-237: "Resource appears anywhere in a nested chain, as ancestor or requested
endpoint: explicitly unsupported; configuration error in either mode", and "Top-level Resources retain their
behavior."

Code evidence:

- `docs/reference/resources.md:355-398` documents "A Resource ViewSet may be the *child* of one or more model
  ViewSets (any depth)", with the `cv_publisher_file = ViewSet(model=PublisherFile, parent=ParentViewSet(name="publisher"), ...)`
  example and "Multi-level model parents (model -> model -> resource) work the same way".
- `tests/test1/test_resource_views.py:163-215` (`test_nested_list_scoped_to_parent`,
  `test_nested_detail_url_contains_parent_pk`, `test_nested_detail_scoped_to_parent_404`) exercise exactly this.
- `ViewSet.checks()` E261 (`src/crud_views/lib/viewset/__init__.py`) encodes the current rule as "Resources can
  only be leaves in the nesting hierarchy (v1)", i.e. a Resource *leaf* is the supported case.

The spec's rationale ("A Resource loads through application code rather than ORM relationships; validating its
membership generically would require a separate explicit contract") is correct for a Resource as an *ancestor*,
which E261 already forbids. For a Resource as the *requested endpoint*, every ancestor is ORM-backed, so the new
traversal can resolve and authorize the whole ancestor chain exactly as for an ORM leaf; the leaf's own membership
in its parent is already the endpoint's job (`ResourceViewMixin.get_queryset()` passes `**self.kwargs` to
`cv_get_items`), just as `ViewSet.get_queryset()` is the ORM leaf's job. Nothing in the ancestor mechanism
needs to validate the Resource row.

Failure scenario: an application using the documented `cv_publisher_file` pattern upgrades; its ViewSet becomes a
configuration error at startup in both cascade modes. There is no P-02 row, no Breaking changelog note and the
"Top-level Resources retain their behavior" sentence reads as if nested leaves never worked.

Suggested resolution: narrow D-29 to "Resource as an ancestor is unsupported (existing E261); a Resource leaf under
an ORM chain participates with its ancestors authorized by the shared traversal and its own scoping unchanged",
or, if the maintainer really wants to drop nested leaves, add a Breaking row, a `docs/migrating-1.0.md` entry and
retire the documented example and tests explicitly.

### 2. High: Guardian child under a core parent flips from object grant to model permission silently

Spec lines 34 (D-06), 165-166, 453-455, 693 (P-02 row 1: "No explicit old parent-policy settings: use new
ancestor policies; implicit old library defaults do not trigger an error").

Code evidence: `GuardianParentPermissionMixin._guardian_user_has_parent_perm()`
(`src/crud_views_guardian/lib/mixins.py:363-380`) always evaluates the parent with `ObjectPermissionChecker`
(or the child view's global fallback), regardless of whether the parent ViewSet is a `GuardianViewSet` or a core
`ViewSet`. The composition exists in the suite: `tests/test1/test_guardian_delete.py:25-28` builds
`GuardianViewSet(model=Contract, parent=ParentViewSet(name=cv_publisher.name, attribute="publisher"))` where
`cv_publisher` is a core `ViewSet`, and grants access with `assign_perm("view_publisher", actor, publisher_a)`
(line 82), an object grant on the core parent.

Under D-06 the core parent's provider defaults to `model`, so the request gate becomes
`user.has_perm("app.view_publisher")`: users who hold object grants on the parent lose access (403) and users who
hold the model permission gain access, with no error raised, because no removed field was supplied.

Suggested resolution: add a P-02/B-05 row for "Guardian child ViewSet whose ancestor is a core ViewSet" stating the
new semantics and the migration (declare `AncestorPolicy(provider="guardian")` on the parent if it should stay
object-gated, which the C-02 table currently rejects for a core ViewSet, or accept the flip explicitly), and
consider a system-check warning for this composition when the ancestor's `provider` is unset.

### 3. High: child-view `cv_guardian_accept_global_perms` silently loses its parent-check role

Spec lines 46 (D-18), 167-168, 297, 697 (P-02 row: "Existing endpoint view uses `cv_guardian_accept_global_perms`:
keep its independent endpoint-local meaning; this is not one of the removed parent-policy fields").

Code evidence: today the *parent* check honors the *child view's* flag:
`_guardian_user_has_parent_perm()` reads `getattr(cls, "cv_guardian_accept_global_perms", False)` and accepts
`user.has_perm(parent_perm)` (`mixins.py:375-377`); `docs/reference/guardian.md:286-289` documents this ("The
parent check follows the child view's `cv_guardian_accept_global_perms`... a model-level permission on the parent
model is accepted as a fallback"). The spec moves that fallback to the *ancestor's* `AncestorPolicy(accept_global_perms=True)`
with default `False`.

Failure scenario: an application grants `view_publisher` as a model permission and sets
`cv_guardian_accept_global_perms = True` on its nested Guardian book views, as documented. After migration the
view flag is retained (so no P-02 error fires) but its parent-check effect is gone; every nested request is 403
until the maintainer discovers the ancestor-side flag. The spec's "Never silently ignore an explicitly supplied
restrictive old setting" (line 683) covers only restrictive settings; this one is permissive and its scope shrinks
silently.

Suggested resolution: add a P-02 row ("child view `cv_guardian_accept_global_perms` no longer affects ancestor
checks; declare `AncestorPolicy(accept_global_perms=True)` on the ancestor"), a `docs/reference/guardian.md`
update, and have `GuardianManageView._guardian_global_fallback_applicable()` (B-05 diagnostics) stop reporting the
view flag as applicable to the parent check.

### 4. Medium-High: `CrudView.dispatch()` cannot be the single entry point; the spec says "can", the code says "always"

Spec lines 185-187 ("one identifiable enforcement entry point"), 598-601, 624-633 (B-03: step 4 before step 5;
"a denial at an outer selected gate stops processing before probing deeper missing/mismatched objects"), 643
(example: "403 at the denied outer gate; do not inspect the deeper object"), and the section C table ("Django
permission dispatch *can* run `has_permission()` before `CrudView.dispatch()`").

Code evidence: every shipped permission-required class is `X(CrudViewPermissionRequiredMixin, X)` with
`CrudViewPermissionRequiredMixin(PermissionRequiredMixin)` ahead of `CrudView` in the MRO
(`create.py`, `list.py`, `detail.py`, `update.py`, `delete.py`, `action.py`, `form.py`, `card.py`, polymorphic,
object-detail, workflow); `ManageView(PermissionRequiredMixin, CrudView, TemplateView)` likewise. Django's
`PermissionRequiredMixin.dispatch()` therefore always runs first and calls
`CrudViewPermissionRequiredMixin.has_permission()` (`src/crud_views/lib/view/base.py:1077-1088`), which performs
the model permission check (403) and then `cv_get_action_object()` -> `get_object()` / `cv_get_parent_object()`
(404 for a missing or mismatched endpoint object or parent) before `CrudView.dispatch()` (`base.py:262`) is ever
reached. No `as_view()` or `setup()` override exists anywhere in `src/`.

Consequence: with the hook in `CrudView.dispatch()`, B-03's required order (ancestor gates before local permission,
before deeper object probing) is violated for every shipped `*PermissionRequired` view, and the approved example
"outer ancestor denied + deeper object missing -> 403" is unattainable (the request 404s or 403s locally first).
Satisfying B-03 with one entry point requires a hook above `dispatch` (an `as_view()` wrapper on `CrudView` or a
`setup()`-level guard that can return a redirect), or two hooks (one in `CrudViewPermissionRequiredMixin`, one in
`CrudView`), which conflicts with the one-entry-point criterion.

Suggested resolution: change "can run" to "always runs" in section C, and record the constraint as part of the
contract: the enforcement hook must execute before `PermissionRequiredMixin.dispatch()` in every shipped
composition. The exact mechanism stays builder discretion, but the constraint is not.

### 5. Medium: all-none ancestry turns relationship validation into an anonymous existence oracle

Spec lines 58 (D-30: "All-none ancestry adds no login requirement"), 587-588 (step 3 actor policy only "if
protected ancestry is selected"), 603-607, 617, 629-630 (B-03: relationship 404s at step 3, endpoint-local checks
at step 5).

Code evidence: today anonymous requests never observe ancestor existence. For core permission-required views,
`CrudViewPermissionRequiredMixin.has_permission()` returns `False` from `super().has_permission()` before any
object load (`base.py:1078`), so the response is a login redirect regardless of the URL parent. For Guardian
children, `GuardianParentPermissionMixin.dispatch()` denies anonymous and inactive actors before
`_guardian_check_parent()` (`mixins.py:323-331`).

Under the spec, when every ancestor declares `provider="none"`, step 2 is skipped and step 3 resolves the chain
(404 on a missing or mismatched ancestor) before step 5 applies the endpoint's own anonymous redirect. An
unauthenticated client can therefore enumerate ancestor PKs (404 vs 302) on a protected endpoint. The same applies
to inactive users (404 vs 403).

Suggested resolution: state in B-01/B-03 that when the requested endpoint has an authentication requirement of its
own (any `*PermissionRequired` or Guardian composition), the actor policy runs before relationship resolution even
for all-none ancestry; or run relationship validation after local gates for all-none chains; or document the leak
explicitly as accepted.

### 6. Medium: ViewSet-dependent policy validation must precede `register()` or rejected ViewSets leak

Spec lines 380 (`provider="guardian"` on a core ViewSet), 382 (`accept_global_perms=True` with non-guardian
effective provider), 386-388 (mechanisms), 694-695 (P-02 subclass field declarations).

Code evidence: `ViewSet.register()` is a `model_validator(mode="after")` that inserts `self` into `_REGISTRY` and
creates `AutoManageView` (`src/crud_views/lib/viewset/__init__.py`, `register`). The existing
`GuardianViewSet.reject_removed_global_perms_flag` is deliberately a *before* validator and its docstring records
why: "Raising here precedes the after-validator, so nothing is registered." The three C-02 rows above depend on the
owning ViewSet class, so they cannot live in `AncestorPolicy`'s own validation; if they are implemented as an
after-validator declared after `register()`, a rejected `ViewSet(...)` call leaves a registered name behind.

Failure scenario: a test or application constructs a ViewSet with `AncestorPolicy(provider="guardian")` on a core
ViewSet, gets the configuration error, fixes it and retries: "ViewSet name ... is already registered". Leaked
registrations also feed `ViewSet.checks_all()` and `check_guardian_composition()`, the contamination the spec's
section G warns about.

Suggested resolution: add to C-02: owning-class-dependent validation runs before registration (before-validator
or a validator ordered ahead of `register()`), or registration is rolled back on failure.

### 7. Medium: nested manage views acquire a new gate while the spec says the manage gate must not change

Spec lines 524-525, 536 ("Built-in manage views: read for ancestry; keep the existing independent manage gate"),
613 (anonymous -> login redirect), 722 ("Do not change ManageView's administrative gate").

Code evidence: `ViewSet.register()` auto-registers `AutoManageView` for every ORM ViewSet, nested ones included;
`get_path_parent()` puts the parent PKs into its URL. `ManageView.has_permission()`
(`src/crud_views/lib/views/manage.py:32-39`) returns `True` for everyone, anonymous included, when
`CRUD_VIEWS_MANAGE_VIEWS_ENABLED="yes"` (the test project's value, `tests/test1/conftest.py:123`) and never resolves
the parent PK. `GuardianManageView` has no Guardian mixins and no parent check today.

Under the spec a nested manage page newly requires authentication (B-01 default redirect), `view` on every
selected protected ancestor, and returns 404 for a nonexistent parent PK, in all three `MANAGE_VIEWS_ENABLED`
modes. That is a change to the manage access policy, which the spec elsewhere forbids. The manage page renders
configuration, not parent data, so either outcome is defensible, but it must be decided.

Suggested resolution: either exempt manage views from ancestor traversal (classify as "no ancestor requirement"
rather than Read) or amend line 722 to record that nested manage pages now inherit ancestor read gates and
login.

### 8. Medium: `RedirectChildView` is missing from the B-02 family table

Spec lines 528-549 (B-02 table), 537 ("Generic ActionView, object/no-object custom forms, workflow, other custom
endpoints: explicit ViewSet action declaration required"), 17 (D-17).

Code evidence: `src/crud_views/lib/views/child.py` ships `RedirectChildView(CrudView, SingleObjectMixin,
RedirectView)` with `cv_key="redirect_child"`, `cv_backend_only=True`, exported from `crud_views.lib.views`. It
resolves its object and redirects to a child collection URL. It is a package view, not a custom endpoint, yet it
has no family in B-02. Registered on a nested ViewSet (Book under Publisher redirecting to BookNote, the pattern
`tests/test1/app/views.py:1060` sets up for breadcrumbs), the implementer must either guess a family (which D-17
forbids) or force the application to declare `actions={"redirect_child": ...}` for a shipped view.

Suggested resolution: add a row ("Built-in child redirect: Read") or list it explicitly as declaration-required.

### 9. Low-Medium: C-02 does not say what happens to request-side declarations on a ViewSet with no parent

Spec line 64 (D-36: "reject invalid or ineffective configuration"), 298-301 (cascade/read/write/actions describe
"requests targeting this ViewSet"), 526 ("Unknown-action checks apply to nested endpoints ... not top-level
actions"), 582 ("Top-level endpoints perform no ancestor loading").

Code evidence: a top-level `ViewSet(model=Author, name="author")` has no ancestors, so `cascade`, `read`, `write`
and `actions` on it can never take effect. The C-02 table lists `accept_global_perms` without a guardian provider
as "ineffective, error" but is silent about these four. Two implementers would reasonably produce opposite
behavior (error vs silently ignored), and the silent variant hides a misplaced declaration (the policy written on
the parent instead of the child).

Suggested resolution: add a C-02 row for "cascade/read/write/actions declared on a ViewSet without a parent"
(error, warning or ignored) consistent with D-36.

### 10. Low: `actions` key validation vs the `list` to `card` alias

Spec lines 301, 383 ("Action key not registered on its owning ViewSet: configuration error once view registration
is complete").

Code evidence: `ViewSet.get_view_class()` and `get_router_name()` resolve the key `"list"` to the registered
`"card"` view when no list view exists (cards-first ViewSets, `src/crud_views/lib/viewset/__init__.py`). Whether
`actions={"list": ...}` on such a ViewSet is "registered" is undefined by the spec. B-02 already classifies card
as Read, so the practical risk is only an inconsistent error, but the rule should state that only literal
registered keys count (recommended) or that the alias applies.

### 11. Low: migration table omits the startup-breaking custom-action requirement

Spec lines 45 (D-17), 59 (B-02), 689-697 (P-02 table lists only Guardian settings), 684-687.

Under D-17/B-02 every nested `ActionView`, `CustomFormView`, `CustomFormNoObjectView`, `WorkflowView` and
other custom endpoint without an `actions` entry is a configuration error (system check plus runtime guard) in both
cascade modes. This affects core applications that never used Guardian, so it is outside the P-02 Guardian table,
yet it is the most likely upgrade failure for such applications. Line 686 mentions "action declarations" among
things to document, but the migration table and the Breaking entry should name it.

### 12. Low: example import path for `ParentViewSet`

Spec line 328 imports `from crud_views.lib.viewset.parentviewset import ParentViewSet`, while
`crud_views.lib.viewset` already exports it (`src/crud_views/lib/viewset/__init__.py:35`) and the test
application imports it from there (`tests/test1/app/views.py:30`). Since C-03 makes `crud_views.lib.viewset` the
public location for the new types, the example should import `ParentViewSet` from the same module to avoid
suggesting a second public path.

## Addendum claims verified against source

The technical addendum (sections B-G) was spot-checked; the following statements match the current code and need
no change: `ViewSet` registry and `register()` behavior; `get_parent_url_args` / `get_parent_attributes` /
`get_queryset` chain filtering with no authorization; `ParentViewSet` defaults; `CrudView.dispatch()`
responsibilities; `cv_get_parent_object()` immediate-parent-only `get_object_or_404`;
`CrudViewPermissionRequiredMixin.permission_required` asserting on a missing key and `has_permission()` running the
model check then `cv_get_action_object()` + `cv_action_enabled()`; all `GuardianParentPermissionMixin`,
`GuardianObjectPermissionMixin` and `GuardianQuerysetMixin` behaviors listed in section D, including the global
fallback trap; `_cv_guardian_create_parent()` M2M denial; `GuardianViewSet.default_permissions` using guardian's
content type; `STRICT_HELPER_POLICY`; `reject_removed_global_perms_flag`; the list of consumers of the removed
fields (dispatch, child link access, create button context, cancel helpers, create access helpers, manage view
and `config_table.html`, `crud_views_guardian.E001`); `CardListView` deriving from `CrudView` + Django `ListView`;
`PolymorphicCreateSelectView(CrudView, generic.FormView)`; `FormSetMixinBase.get()` fragment ordering; settings
captured at import in `CrudViewsSettings`.

## Conventions check

Repository `CLAUDE.md` rules were checked against the spec: the maintainability decision rule is reinforced
rather than violated; the `cv_` prefix convention applies to CrudView attributes and the new declarations live on
the ViewSet (Pydantic fields, consistent with `parent`, `ordering`, etc.); the "Breaking entry requires
`docs/migrating-1.0.md`" rule is acknowledged at line 686-687. Findings 1, 2, 3 and 11 identify Breaking
behavior that the current migration section does not yet enumerate, which that rule will require.
