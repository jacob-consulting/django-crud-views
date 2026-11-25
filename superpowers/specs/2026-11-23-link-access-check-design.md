# Concept: one link access check, shared grants, and what is deliberately left out

Date: 2026-11-23. Status: concept approved by the maintainer on 2026-11-23; **no implementation is authorized by this
document**. It is not an implementation plan. Each stage in section 9 needs its own issue, plan and approval.
Amended on 2026-11-23 for stage 1: section 12.6 (D-25 to D-36), decided by the maintainer while #407 was planned.
Amended on 2026-11-24 for stage 2: section 12.7, findings F-01 to F-08 from a probe after stage 1 shipped, and
D-37 and D-38, decided by the maintainer. The "to verify" items of 12.3 are answered there.
Amended on 2026-11-24 for stage 3: section 12.8 (D-39 to D-55), decided by the maintainer after a review of #411;
D-55 was added while #412 was planned.

Related: #385 (reuse Guardian grants), #314 (opt-in URL helper), #312/#318 (link visibility versus request gate),
`superpowers/notes/2026-11-02-navigation-concept-exploration.md` (site menu, caching options C0–C6),
`superpowers/notes/2026-11-04-opt-in-url-helper-decision.md` (maintainability rule).

Line references are `main` @ `7c8e0177`.

## 1. Intent

The package decides in about ten places whether a link or button to a view is shown. Each place calls the checks
itself and passes "the object" with a different meaning. A site menu and permission-aware breadcrumbs are coming and
would add two more. The same Guardian grants are also loaded repeatedly within one request.

The concept gives the package:

- one function that decides a link, built from the pieces the request gate already uses;
- one shared Guardian checker per user and request;
- a written position on business checks, cross-request caching and full-hierarchy checks, so later work attaches to
  a defined place instead of being patched in.

The overriding constraint is the project's decision rule: the result must stay understandable, explainable and
maintainable by the maintainer.

## 2. Goals, non-goals, anti-goals

**Goals**

- A link is decided the same way everywhere: context buttons, row actions, card actions, object navbar, cancel
  target, bulk toolbar, breadcrumb, and later the site menu.
- Remove the repeated Guardian grant queries within a request (#385).
- Keep `cv_has_access` and `cv_action_enabled` as the project extension points.
- Define, without building, how a full-hierarchy check and a cross-request cache would attach.

**Non-goals**

- Rewriting the request gate.
- Building the site menu. This concept only fixes what the menu will call.
- A cross-request cache in the first version.
- Query-free pages. The request gate always reads grants fresh.
- Deriving a ViewSet from a model.

**Anti-goals** (would make the work a failure even if it passes tests)

- A cached or stale value ever granting access. A wrong link may be shown or hidden; a request is always checked
  completely and fresh.
- Stand-in or fake view instances created only to satisfy a hook signature.
- State (business) rules ending up in any cache.
- Hidden ambient state (context variables, middleware-installed globals) as the way checks reach shared data.

## 3. How it works today

Two separate paths exist.

**Request gate.** `CrudView.dispatch` → `_cv_ancestor_guard` → `_authorize_ancestors`
(`src/crud_views/lib/ancestors.py:464`) loads every ancestor through its ViewSet queryset and runs the selected
permission gates, then `CrudViewPermissionRequiredMixin.has_permission` (`src/crud_views/lib/view/base.py:1295`)
checks the view's own permission and `cv_action_enabled`. It is covered by 18 `tests/test1/test_ancestor_*.py`
files, `test_access_trace_ancestors.py` and the access trace.

**Link path.** The class methods `cv_has_access(user, obj)` and `cv_action_enabled(user, obj)`, plus three private
adapters (`_cv_child_link_has_access`, `_cv_action_enabled_for_context`, `_cv_action_enabled_for_rendering`). Call
sites: four context button classes (`src/crud_views/lib/view/buttons.py:109-114, 184-189, 238-242, 297-301`), row
actions (`base.py:910-913`), card actions (`src/crud_views/lib/views/card.py:63-64, 86-87`), object navbar
(`src/crud_views/lib/navbar.py:84-87`), cancel target (`base.py:76-88`), bulk toolbar
(`src/crud_views/lib/bulk/__init__.py`), and the `cv_context_has_permission` filter
(`src/crud_views/templatetags/crud_views.py:650-655`).

Guardian adds its own pieces to this path, and stage 3 must cover each of them:

- `GuardianQuerysetMixin.cv_get_context` (`src/crud_views_guardian/lib/mixins.py:307-358`) rewrites `cv_access` and
  `cv_action_enabled` after the fact for a child create rendered on a list page, because the class method cannot
  see the parent.
- Three `_cv_cancel_target_available` overrides (`mixins.py:116, 258, 440`) and `_cv_cancel_parent_target_access`
  (`mixins.py:464`).
- The create views' adapter overrides, which resolve the parent from the rendering view with a fallback query
  (`src/crud_views/lib/views/create.py:36-75`, `src/crud_views_guardian/lib/views.py:305-313`).

Observations that drive the design:

- `obj` means "the target's own object", "the parent" or "nothing" depending on the caller. A child link passes the
  parent as `obj` (`base.py:528-530`); the Guardian child create documents four cases for it
  (`src/crud_views_guardian/lib/views.py:347-383`). The adapters exist to bridge these meanings.
- Links check only the immediate parent (`_immediate_parent_access`, `ancestors.py:654`); the request checks the
  whole chain.
- The breadcrumb checks no permission and loads each ancestor again
  (`src/crud_views/lib/breadcrumb.py:206-275`).
- Context buttons and row actions evaluate state before permission, so a denied button still pays for its state
  rule.
- Django model permissions are already shared per request: Django keeps the permission set on the user object (two
  queries for any number of checks).
- Guardian grants are not shared. `ObjectPermissionChecker(user)` is built in four places, all in
  `crud_views_guardian`: `lib/mixins.py:156, 213` and `lib/ancestors.py:67, 70`. Only the ancestor gate reuses one,
  per view. #385 measured 26 queries with a four-item navbar against 18 without, on a warm second request.
- Nothing in `src/` uses Django's cache framework.
- The workflow, polymorphic and object-detail apps have no permission machinery of their own; their views use the
  core mixin with a permission key. Workflow's per-transition check runs only on the workflow page.

## 4. Approaches considered

**A. Shared checker only.** Put the Guardian checker on the user object; change nothing else. Smallest change and
it fixes #385's measured waste. The ten call sites keep their differing meanings of `obj`, the adapters stay, and
menu and breadcrumb each invent their own way of calling the checks.

**B. Shared checker plus one link check (chosen).** One function runs parent gates, own permission and state, built
from the pieces the gate already uses. All link consumers move to it. The gate is untouched. One place to read and
explain; breadcrumb and menu use it directly; the later extensions have a defined place. It touches every link call
site and narrows the meaning of `obj`.

**C. Full unification.** As B, and the request gate is rewritten to run through the same function. One evaluator
for everything, at the price of rewriting the most heavily tested path for no user-visible gain. Rejected under the
rule to preserve proven code paths.

The maintainer chose B, delivered in stages (section 9). Without the site menu on the roadmap, A alone would have
been the recommendation: nearly all measurable gain comes from the shared checker, and the link check is an
investment in consistency.

## 5. The link check

### 5.1 Question and answer

Input, always named by the caller:

- the user;
- the target view class (which fixes the ViewSet and key);
- the target's own object, or none;
- a list of known ancestor objects, nearest first, possibly empty.

The check itself takes no view. A consumer on a CRUD page fills the ancestor list from its own view's resolved
ancestors before calling. Assistant's call: the rendering view may additionally be passed through, as the real view
or as nothing on a non-CRUD page, only for existing hooks that already accept it (`cv_create_has_access`). It is
never fabricated.

Output: allowed, denied by permission, or denied by state. This is what the existing hide/disable handling
(`src/crud_views/lib/view/visibility.py`) already consumes.

### 5.2 Three steps, in the request's order

1. **Parent gates.** For each ancestor in the list, the gate the request would run at that level, using the same
   pieces: `_selected_gates`, `_operation_requirements`, `_permission_name` and the provider's
   `_ancestor_has_permission`. The two rules today's parent check also applies are kept: the actor must be signed
   in and active for protected ancestry (`base.py:539-541`), and `_check_nested_auth` (`ancestors.py:683`).
   Assistant's call, matching today (`ancestors.py:672-673`): a nested target whose immediate parent is not in the
   list is denied. Only ancestors above the nearest one may be absent and are then unchecked.
2. **Own permission.** `cv_has_access(user, obj)` of the target view, where `obj` is only ever the target's own
   object.
3. **State.** `cv_action_enabled`, evaluated only when steps 1 and 2 passed. Maintainer decision: the object it
   receives follows the request's definition in `cv_get_action_object` (`base.py:568-575`): the target's own object
   for an object view, the immediate parent for any nested view without an own object (list and create alike),
   otherwise nothing. Today buttons pass the page object or nothing there (`buttons.py:109-111, 297-299`,
   `base.py:910`), so this is a second change to a public hook and lands together with the narrowing in 5.6.

### 5.3 Which ancestors are checked

Maintainer decision: a link checks the ancestors it is handed, plus any higher ancestors the current request has
already resolved (`_cv_ancestor_state`). It never loads an ancestor only to decide a link.

- Direct children of an object in hand (for example a tenant in the menu): the link check and the request ask the
  same question.
- Links on a nested page: the guard has loaded every ancestor of the page, and with shared grants checking them
  costs no query.
- Unchecked: a deep link whose higher ancestors are not on the current page (for example a dashboard listing rows
  from several parents). This is the off-page case of #314; the caller supplies context explicitly.

### 5.4 Accepted difference from the request

The request loads each ancestor through its ViewSet's `get_queryset(view)`, which a project may override to hide
archived or soft-deleted rows; the request then answers 404. A link does not consult those querysets. Maintainer
decision: this is accepted. Such a link can only arise when the page obtained the object outside the ViewSet scope
(its own query, `user.tenant`, an email). The failure is always a refused click, never access to data.

No link check can see a project's `has_permission()` or `dispatch()` override, Guardian list filtering, or
middleware. For a Guardian list the link is shown to everyone except an inactive signed-in user, anonymous users
included (`crud_views_guardian/lib/mixins.py:288-294`); sign-in is required only on the nested child-link path
(`mixins.py:300`), and the queryset filters the rows. These stay documented limits. The site menu needs its own
signed-in rule for Guardian list items, as the navigation exploration already decided.

### 5.5 Relation to the request gate

Assistant's call, not objected to: the gate is not rewired. "One rule" means the link check is assembled from the
gate's existing building blocks, as `_immediate_parent_access` already is. Gate order, 404 versus 403, login
redirects and trace recording stay exactly as they are.

### 5.6 Project hooks

`cv_has_access` and `cv_action_enabled` remain the public extension points. One meaning changes: `obj` in
`cv_has_access` is only the target's own object. The parent no longer arrives there; it is handled by step 1. Assistant's call: a target without an own
object (list, create) therefore receives `None`, where callers pass the page object today (`buttons.py:114`,
`base.py:913`). A project override that read the page object there is affected and belongs in the Breaking entry.

Maintainer decision: this narrowing lands **before 1.0**, with a `### Breaking` entry in `CHANGELOG.md` and an
entry in `docs/migrating-1.0.md` covering both hooks (`cv_has_access` here, `cv_action_enabled` in 5.2).

The narrowing cannot ship alone. A nested Guardian create has no permission of its own; its whole rule is the
parent rule, which it receives through `obj` today, and it answers `False` for an empty `obj`
(`crud_views_guardian/lib/views.py:382-383`). Once `obj` no longer carries the parent, `False` would make step 2
deny every such link, and `True` would make every direct caller of the hook (the template filter,
`SiblingContextButton`, project code) show the button without a parent check. Maintainer decision: the core of the
link check is therefore pulled forward to before 1.0 as a private function, and the package's own callers that pass
a parent go through it in the same change. Constraints for that stage's plan:

- a direct call to `cv_has_access` on a nested Guardian create must not start answering "allowed" without a parent
  check;
- `cv_create_has_access(user, rendering_view, parent_obj)` stays the documented hook for parent-based create rules
  and keeps being called, with the real rendering view or nothing;
- how step 2 is satisfied for a view whose only rule is the parent rule is left to that plan.

Known sites: `_cv_child_link_has_access`
(`base.py:528-541`), the Guardian child create's `cv_has_access` cases 3 and 4 and its `_cv_child_link_has_access`
(`crud_views_guardian/lib/views.py:347-388`), the Guardian queryset mixin's `_cv_child_link_has_access`
(`crud_views_guardian/lib/mixins.py:297-305`), and `docs/reference/guardian.md` ("Create button visibility for
child viewsets"). `cv_create_has_access(user, rendering_view, parent_obj)` already receives the parent explicitly
and is the hook a project uses for parent-based create rules. This is more than a one-line change; its exact shape
belongs to that stage's plan.

## 6. Business checks

Maintainer decision: two classes of rule, which is the split the code already has.

| | Cheap state rule | Expensive business check |
|---|---|---|
| Hook | `cv_action_enabled(user, obj)` | `cv_bulk_check(obj)`, form validation, a delete's confirm page |
| Runs | for the link and again for the request | only when the user enters the action, and again inside the write |
| Contract | read fields of the object in hand; no queries | free |
| User sees | button hidden or disabled | the reason, on the page where they can act on it |
| Cached | never | never |

Rule for projects: a check too expensive to run per row belongs on the action's page, not behind the button. Delete
needs nothing new. The default `cv_action_enabled` returns `True`, so an application with few rules pays almost
nothing.

## 7. Sharing within a request

| What | Where it lives | Change |
|---|---|---|
| Django model permissions | on the user object (Django) | none |
| Resolved ancestors | on the view (`_cv_ancestor_state`) | breadcrumb should reuse them (verify the saving) |
| Guardian grants | new: one `ObjectPermissionChecker` on the user object | replaces the four construction sites |

Maintainer decision: the Guardian checker lives on the user object, reached through one small helper. Reasons:
every hook already receives `user`, so no signature changes; it is what Django does with its permission set; it
works for class-level checks and for a menu on a non-CRUD page. The view-local ancestor checker
(`_cv_guardian_ancestor_checker`) is replaced by it.

Known cost, to be documented: a user object kept alive beyond one request (tests, a shell, background tasks) keeps
its old grants, exactly as Django's `has_perm` does. Each normal request builds a fresh user, so a revoked grant
takes effect on the next request.

On list and card pages the shared checker can load the grants for all rows of the page in one step
(`prefetch_perms`). Expected: about two queries per page instead of two per row. Not measured.

Decisions (answer per view and object) are not stored. They are cheap to recompute from shared grants, and storing
them is where state rules could be cached by accident.

Optional fix, only if it proves to be a problem: the manage action's group-membership query runs per check
(`ManageView._cv_manage_allowed`) and could be loaded once onto the user object.

## 8. Specified only, not built

### 8.1 Cross-request cache

Maintainer decisions: revocation must take effect immediately, so the request gate never reads a cross-request
cache; only link rendering may. Specified only; decided again after a real menu has been measured.

With the gate reading fresh and links reusing what the gate loaded, the cache can only save grants the page's own
gate did not load. Reasoned, not measured:

| Page | Would save |
|---|---|
| CRUD page on Django permissions | nothing |
| Page nested under the menu's object | nothing for that menu section |
| Non-CRUD page with the menu | 2 queries (Django permissions) + 2 per Guardian object in the menu |
| Guardian list page | the 1–2 queries for row grants |

Costs: a shared `CACHES` backend; complete signal coverage; and a second way to obtain grants that the gate must
never see, which works against the single check.

If built: opt-in, default off. Content is grants only (a user's permission set; a user's grants on one object).
Invalidation by one global permission counter that is part of every key, bumped on any change to user permissions,
group membership, group permissions, Guardian user or group grants, and a user's active/superuser flags. A short
timeout as a safety net, because bulk writes and raw SQL fire no signals (whether Guardian's bulk assignment fires
signals must be checked). Per-user invalidation was considered and set aside: a group permission change affects
every member.

### 8.2 `force_full_hierarchy_check`

Maintainer expects this to be needed; specified now so it is additive later. Assistant's call on timing: built at
the first real case.

Because the check takes a list of ancestors, the flag only changes who fills the list. With it on, the list is
completed by following the declared foreign key (`ParentViewSet.get_attribute()`) upward from the nearest known
ancestor, and step 1 runs on every level.

- Guarantee: every ancestor's permission gate is checked. It does not guarantee the ancestor is visible through its
  ViewSet queryset (section 5.4).
- Cost: one query per level per distinct parent, plus two for a Guardian ancestor; a list with rows from different
  parents pays per row unless the queryset uses `select_related`.
- A many-to-many parent cannot be derived from a child: deny.
- Estimate from reading the code, not from a prototype: about 40 lines for the walk, 10–20 for the flag, 150–300
  lines of tests. Where the flag is declared (per call, per ViewSet policy, or a setting) is open.

### 8.3 View-free scope hook

If a project ever needs links to honour ViewSet queryset filters, the clean route is a new ViewSet method that takes
only the request and returns the row scope, with `get_queryset(view)` calling it. It adds public surface and
projects would move existing filters into it. Rejected alternative: passing a stand-in view to `get_queryset(view)`.

## 9. Consumers and stages

| Consumer | Change |
|---|---|
| Context buttons, row actions, card actions, object navbar, cancel target, bulk toolbar, template filter | call the one check; state evaluated only after permission passes |
| Request gate | none |
| Breadcrumb | each item goes through the check; a denied item renders as plain text, not a link; reuses resolved ancestors |
| Site menu (later) | an item is a target view plus an optional ancestor list; plain URL items carry a permission name; own design |
| Delete preview | none; remains the only place that maps a model to a ViewSet |
| Manage page, `cv_access`, `cv_manage_view` | none; the published JSON formats are unchanged because the gate is unchanged |
| Workflow, polymorphic, object-detail | none of their own; they follow the core |

Stages, each shippable on its own:

1. **Before 1.0:** the link check as a private function; the child-link and create call sites, core and Guardian,
   moved to it; `obj` narrowed in `cv_has_access` and aligned in `cv_action_enabled` (sections 5.2 and 5.6). This is
   a real piece of work on the 1.0 path, not a one-line change.
2. **Shared Guardian checker on the user object** (approach A). Closes the within-navbar part of #385. Independent
   of stage 1 and may ship before or after it.
3. **The remaining consumers** moved to the check one at a time, and the check made the documented way to decide a
   link. The adapters are expected to become unnecessary; this must be proven per consumer, including the Guardian
   pieces listed in section 3.
4. **Breadcrumb** through the check.
5. **Site menu** on top, with its own design.

Later, on demonstrated need: section 8.2, then 8.1, then 8.3.

## 10. The three identity questions

- **What is the ViewSet of a model?** The check never asks. Every consumer names a target view class, and the class
  carries its ViewSet.
- **What is the parent ViewSet?** The declared `ViewSet.parent`, walked by `_walk_ancestors`. Nothing is inferred
  from model relations.
- **One model in several ViewSets?** The caller names the target, so there is no ambiguity. An object alone cannot
  choose among ViewSets; this matches #314. The delete preview is the single exception and is left as it is.

## 11. Left to the builder, and to verify

- The name, module and exact signature of the check and of the checker helper.
- Whether the adapters can be removed entirely (stage 3).
- The breadcrumb's saving from reusing resolved ancestors.
- Query counts before and after each stage, pinned in the existing cost tests
  (`tests/test1/test_navbar_costs.py`, `tests/test1/test_ancestor_costs.py`); all figures here other than #385's 26
  and 18 are projections.
- Golden files under `tests/test1/golden/` must stay byte-identical for every stage that does not intend a markup
  change.
- Whether stage 2 also changes how `get_objects_for_user` based list filtering interacts with the checker: not
  examined.

## 12. gsd-handover

The maintainer approved this concept on 2026-11-23. The decisions below are settled input for planning. A planner
does not reopen them; a decision changes only when the maintainer says so. No issue has been created yet, and no
stage is scheduled by this document.

### 12.1 Settled decisions

Decided by the maintainer in discussion:

| # | Decision | Section |
|---|---|---|
| D-01 | Approach B: a shared Guardian checker plus one link check. Delivered in the stages of section 9. | 4, 9 |
| D-02 | The request gate always reads grants fresh. A revoked permission takes effect on the next request. | 8.1 |
| D-03 | A cross-request cache may serve link rendering only, never the gate. It is specified, not built, and is decided again after a real menu has been measured. | 8.1 |
| D-04 | A link checks the ancestors it is handed plus those the current request already resolved. It never loads an ancestor only to decide a link. | 5.3 |
| D-05 | Links to ancestors that a ViewSet queryset filters out (archived, soft-deleted) are accepted. Links do not consult ViewSet querysets. The failure is a refused click. | 5.4 |
| D-06 | No stand-in or fake view instances, for any purpose. | 2, 8.3 |
| D-07 | `force_full_hierarchy_check` is specified as a foreign-key walk over permission gates, with many-to-many parents denied. The check's ancestor-list interface is fixed now so the flag is additive. | 5.1, 8.2 |
| D-08 | Business rules split in two: cheap state rules (`cv_action_enabled`) run for links and requests and are never cached; expensive checks run only on the action's page. Delete gets no new hook. | 6 |
| D-09 | The shared Guardian checker lives on the user object. | 7 |
| D-10 | Manage page, `cv_access` and `cv_manage_view` change only if something there needs fixing. Their published JSON formats stay as they are. | 9 |
| D-11 | `obj` in `cv_has_access` is narrowed to the target's own object before 1.0. | 5.6 |
| D-12 | Because D-11 cannot ship alone, the core of the link check is pulled forward to before 1.0 as a private function, and the package's child-link and create call sites move to it in the same change. | 5.6, 9 |
| D-13 | The object passed to `cv_action_enabled` for a link follows the request's `cv_get_action_object`. It lands with D-11. | 5.2 |

Proposed by the assistant and approved with the document:

| # | Decision | Section |
|---|---|---|
| D-14 | The request gate is not rewired. The link check is assembled from the gate's existing building blocks. | 5.5 |
| D-15 | A target without an own object receives `None` in `cv_has_access`. | 5.6 |
| D-16 | A nested target whose immediate parent is not known is denied. Only ancestors above the nearest may be absent. | 5.2 |
| D-17 | The check takes no view. The real rendering view may be passed through to hooks that already accept one, or nothing on a non-CRUD page. | 5.1 |
| D-18 | Step 1 keeps the signed-in-and-active rule for protected ancestry and `_check_nested_auth`. | 5.2 |
| D-19 | State is evaluated only after parent gates and own permission have passed. | 5.2 |
| D-20 | Decisions (the answer per view and object) are not stored anywhere; only grants are shared. | 7 |
| D-21 | A denied breadcrumb item renders as plain text, not as a link. | 9 |
| D-22 | `force_full_hierarchy_check` is built at the first real case, not in the first version. | 8.2 |
| D-23 | If the cross-request cache is ever built, it is opt-in, holds grants only, and is invalidated by one global permission counter plus a short timeout. | 8.1 |
| D-24 | The delete preview stays the only place that maps a model to a ViewSet. | 9, 10 |

### 12.2 Scope of the first phase (stage 1, before 1.0)

In scope:

- The link check as a private function with the inputs of section 5.1 and the steps of section 5.2.
- The call sites that pass a parent today, core and Guardian, moved to it: `_cv_child_link_has_access` and its
  callers, the Guardian child create's access cases, and the Guardian pieces listed in section 3 as far as they
  concern child links and creates.
- D-11, D-13 and D-15 applied to the two public hooks, with one `### Breaking` entry in `CHANGELOG.md`, the matching
  entry in `docs/migrating-1.0.md`, and the affected reference pages.

Constraints the plan must satisfy:

- A direct call to `cv_has_access` on a nested Guardian create never starts answering "allowed" without a parent
  check.
- `cv_create_has_access(user, rendering_view, parent_obj)` stays the documented hook for parent-based create rules
  and keeps being called.
- The request gate, its order, its responses and its trace recording are unchanged (D-14).
- Golden files stay byte-identical unless the plan names an intended markup change.
- Query counts are pinned before and after in the existing cost tests.

Out of scope for stage 1: the shared Guardian checker (stage 2), the remaining consumers (stage 3), the breadcrumb,
the site menu, and everything in section 8.

Section 12.6 amends this scope: D-25 settles which test expectations may be rewritten, D-26 limits which ancestors
the stage-1 call sites hand over, and D-29 adds three callers from the stage-3 list as argument narrowing.

### 12.3 Scope of stage 2 (shared Guardian checker, #385)

Stage 2 is independent of stage 1 and may be planned before or after it. #385 is its issue; that issue's handover
still calls the checker's placement open, which D-09 now settles.

In scope:

- One small helper in `crud_views_guardian` that returns the user's `ObjectPermissionChecker`, creating it on first
  use and keeping it on the user object.
- The four places that build a checker today use the helper: `crud_views_guardian/lib/mixins.py:156, 213` and
  `crud_views_guardian/lib/ancestors.py:67, 70`. The view-local `_cv_guardian_ancestor_checker` is replaced by it.
- Documentation of the lifetime: a user object kept alive beyond one request keeps its old grants, as Django's own
  permission set does.
- The measured-cost table in `docs/reference/navbar.md` and the pinned counts in `tests/test1/test_navbar_costs.py`
  and `tests/test1/test_ancestor_costs.py`, updated to the new figures.

Constraints the plan must satisfy:

- Every access decision is unchanged for every actor: anonymous, inactive, superuser, direct grant, group grant and
  model fallback. Only query counts change.
- Each destination still applies its own permission and its own state rule (#385, decision 4). Sharing loaded
  grants must not make one item's answer stand in for another's.
- The request gate reads grants loaded in the same request, never from an earlier one (D-02).
- The access trace output is unchanged.
- No `### Breaking` entry is expected. If the plan finds one, it stops and reports it.

Out of scope for stage 2: the link check, any Django cache, storing decisions, and top-level navigation.

To verify during planning:

- That keeping an attribute on `request.user` survives Django's lazy user wrapper and behaves for the anonymous
  user. Not checked for this concept.
- Whether loading the grants for all rows of a list or card page in one step (`prefetch_perms`) belongs in this
  stage. The saving is expected, not measured; the planner includes it only with a pinned before-and-after count.

Section 12.7 adds what a probe found after stage 1 shipped: one stage-1 test that contradicts D-09, the tests and
passages the plan must list, D-37, which states one exception to the first constraint above, and D-38, which
answers the `prefetch_perms` item. The first "to verify" item is answered there by reading and by the probe.

### 12.4 Stages 3 to 5 are deliberately unscoped

Stages 1 and 2 have scope blocks because the decisions above determine them fully. The later stages do not, and the
missing blocks are intentional. A planner does not fill them in; each is scoped when what it waits for exists.

- **Stage 3 (remaining consumers)** waits for stage 1's result: which of the three private adapters could be
  removed, and which Guardian pieces still need their own handling.
- **Stage 4 (breadcrumb)** waits for the measured saving from reusing resolved ancestors, and for a look at a
  denied item rendered as plain text on a real page.
- **Stage 5 (site menu)** waits for its own design, built on
  `superpowers/notes/2026-11-02-navigation-concept-exploration.md` and its decisions of 2026-11-02.

Section 12.8 scopes stage 3, now that stages 1 and 2 have shipped, and replaces the stage-3 bullet above. Stages 4
and 5 stay unscoped.

### 12.5 Open for the planner

These are the planner's to decide, within the decisions above:

- Name, module and exact signature of the check.
- How step 2 is satisfied for a view whose only rule is the parent rule (the nested Guardian create).
- Which of the three private adapters can be removed in stage 1 and which must wait for stage 3.
- The exact wording and extent of the Breaking entry.
- The remaining items of section 11.

### 12.6 Stage 1 amendments (2026-11-23)

Planning research for #407 (phase 06.48) found that existing tests and reference pages pin behaviour that sections 5
and 12.1 change, and that two statements of this document cannot both hold in stage 1: D-04 with sections 5.1 and
5.3 (a link also checks the higher ancestors the request resolved) against "the rendered result is the same as
before for every actor" and the pinned gate counts. Checking higher ancestors "costs no query" only once stage 2's
shared checker exists.

The maintainer decided the following on 2026-11-23. The decisions apply to stage 1 only. Where they differ from
sections 5 and 12.2, they apply. Like the decisions in 12.1, they are settled input and are not under review
(section 13, point 1).

| # | Decision | Amends |
|---|---|---|
| D-25 | Request-gate expectations in the ancestor suites stay untouched. Assertions on link helpers in those suites (direct `cv_has_access` calls with a parent or an own child on a nested Guardian create, and the private adapters called by name) are rewritten to the narrowed contract, and the plan lists each rewritten line. `cv_has_access` on a nested Guardian create fails closed for a parent argument; `cv_create_has_access` is the replacement. | 12.2 constraints, 5.6 |
| D-26 | Stage-1 call sites hand the check the immediate parent only, as today. The function gates every level it is handed, proven by a unit test with a two-level list. Filling the list from the request's resolved higher ancestors (5.1, 5.3, second half of D-04) waits for stage 2 or 3. | D-04, 5.1, 5.3 |
| D-27 | On a sibling page the check takes the parent from the parent the request resolved from the URL, not from the page object's foreign key. An explicit condition keeps the two documented `False` answers: the `ManyToMany` child page, and the `cv_context_has_permission` filter on a child list page. | 5.3, 5.6 |
| D-28 | A project's `cv_create_has_access` override governs every package control that links to a nested Guardian create and is shown today; D-33 lists the two that stay hidden. That includes child context buttons, card child actions and object navbar child items, which bypass the hook today, and the create controls reached from sibling pages (D-31). The Breaking entry and the migration note list the sites. | 5.6 |
| D-29 | `ParentContextButton`, the state argument of `SiblingContextButton` and the non-child card action are narrowed in stage 1 as well: argument narrowing only, with no parent-gate step for them. | 9, 12.2 |
| D-30 | The documented Guardian queryset-only exception is kept: the link shows while the request answers 403. | 5.4 |
| D-31 | At the sibling-page sites (context buttons, row actions, the parent button, the sibling button, the non-child card action and the `cv_context_has_permission` filter), only a nested Guardian create target goes through the check. Every other target keeps today's code path with narrowed arguments (D-13, D-15, D-29). Moving those consumers to the check stays in stage 3. For a target that goes through the check, D-16 holds without exception. | 9, 12.2 |
| D-32 | For package links to a nested Guardian create, step 2 asks `cv_create_has_access` only; `cv_has_access` is not called for them. A project override of `cv_has_access` on that view no longer affects package links, and the Breaking entry says so. `cv_has_access` stays step 2 for every other view. | 5.2, 5.6, 12.5 |
| D-33 | A `SiblingContextButton` to a nested Guardian create, and the create control on the nested Guardian create page itself, stay hidden as today. The check is handed no parent for them, so D-16 denies and `cv_create_has_access` is not asked. This adds two kept `False` answers to the two D-27 names and limits D-28 to the controls that are shown today. It can be relaxed after 1.0. | D-27, D-28 |
| D-34 | Known limit L1 is kept in stage 1. `GuardianQuerysetMixin.cv_get_context` matches the resolved key of any context button on a Guardian list or card list page, so a `ParentContextButton(key_target="create")` on a grandchild Guardian list page shows the page's own create result and runs two parent gates; a sibling button registered under the action key `create` there is shown the same way. This is an approved exception to D-28 and D-33 for those controls. It exists before stage 1, removing it would change a rendered result, and section 3 assigns this rewrite to stage 3. The migration note, the Breaking entry and `docs/reference/guardian.md` state it. | 3, D-28, D-33 |
| D-35 | Known limit L2 is kept in stage 1. Today's path for a nested Guardian create under a model-permission parent denies an inactive actor and returns the provider's answer for an anonymous one; the signed-in-and-active rule of the core adapter was never on this path. "Kept" in 5.2 and D-18 means the rules today's parent check applies. | 5.2, D-18 |
| D-36 | On a view that did not run the ancestor guard, a nested list's state hook receives `None`. This narrows D-13; no core control disappears on such a view. | 5.2, D-13 |

Consequences the plan must carry. They follow from the decisions and are not decisions themselves:

- **D-25:** the own-child argument is the planner's to settle within D-11; research recommends that the hook
  answers `False` for every argument. Either way, the passages that say a parent instance "works as before"
  (`docs/migrating-1.0.md`, "Nested Guardian create access") and the input table in `docs/reference/guardian.md`
  ("What the create access helpers accept") are rewritten, not appended to. The change is from allowed to denied.
- **D-26, D-30, D-34 and D-35:** the known limits of D-34 and D-35 are accepted behaviour for a stage-1 review
  in the same way, and not a finding under section 13.
- **D-26 and D-30:** a child link can stay visible where a farther ancestor, or a queryset-only composition, denies
  the request. The click is refused with 403, as documented today. For a stage-1 review this is accepted behaviour
  and not a finding under section 13.
- **D-27:** `docs/reference/context_buttons.md` gives "the filter has no URL parent to work with" as the reason for
  the two `False` answers. That reason no longer holds and is reworded: the two answers are kept on purpose. A view
  without a resolved parent (a custom or non-CRUD view) is denied under D-16, where the foreign-key walk answered
  before; the migration note names this.
- **D-28:** the hook exists only on the Guardian create view, and its `rendering_view` is documented as the list
  view instance. At the three new sites it is a different view, or nothing. The Breaking entry states what an
  override receives there. The rendered result is unchanged only for the default hook, which stays one parent gate.
- **D-29 with D-25:** a narrowed site that reaches a nested Guardian create with `None` would get `False`. Such a
  site goes through the check for that target, and only for that target (D-31); narrowing alone would hide a
  button that shows today.
- **From "the rendered result is the same as before":** sibling-page links to core targets carry no parent gate
  today and get none in stage 1. Gating them is stage 3.

### 12.7 Stage 2 amendments (2026-11-24)

After stage 1 shipped (#409), stage 2 was probed against it. A throwaway helper kept one `ObjectPermissionChecker`
on the user object under the attribute `_cv_guardian_checker`, and the four construction sites used it. The probe
ran in a scratch worktree at `63e8e07d` and was discarded. `pytest tests/test1 -n auto`: 101 failed, 18,661 passed.

Nothing in the stage-1 code blocks stage 2. The link check reaches Guardian only through
`_ancestor_has_permission` and `cv_has_access`, which is where the helper goes. The findings below are input for
the stage-2 plan. They are findings, not maintainer decisions. F-02 raised a question, which the maintainer
decided as D-37 below. No decision is open.

| # | Finding | Kind | Amends |
|---|---|---|---|
| F-01 | `test_no_decision_is_stored` (`tests/test1/test_link_access.py:469, 476`, added in stage 1) asserts that a link check leaves no new attribute with `cv` in its name on the user object. A checker kept on the user (D-09) fails it when the attribute is named in the `cv` style. D-20 forbids stored decisions only; grants are shared. Stage 2 rewrites the assertion to exempt the checker attribute by name and keeps the rest of the test. | contradiction with stage 1 | D-09, D-20 |
| F-02 | `test_guardian_workflow_late_refusal_retains_scoped_authorization[permission-*]` (`tests/test1/test_workflow_review.py:259`) revokes a grant inside the request and expects `PermissionDenied`. The second check is not a guard inside the write. When a business rule refuses the transition, the transaction unwinds and `WorkflowView.post` reloads the object to render the form with the error (`src/crud_views_workflow/lib/views.py:101`); on a Guardian view that reload runs `_check_object_perm` again through `get_object`. No write follows it. With the shared checker the reload reads the grants loaded earlier in the same request and the form is shown. Settled by D-37. | decided | 12.3 constraints, D-02 |
| F-03 | Count pins outside the two files 12.3 names: five tests in `tests/test1/test_guardian_child_link_visibility.py` (`test_query_cold_and_warm_discovery[context, card]`, `test_query_create_uses_only_its_existing_parent_check[context, card]`, `test_query_unaffected_core_and_ordinary_actions`) pin `permissions: 2` or `permissions > 0` and see none. The plan lists them with the new figures. | expected, scope addition | 12.3 scope |
| F-04 | `test_navbar_isolated_costs` (`tests/test1/test_navbar_costs.py:165`): all 80 cases drop from 4 queries to 2 or 0. `tests/test1/test_ancestor_costs.py` did not fail; its counts may not change, because the ancestor gate already reuses one checker per view. | expected | 12.3 scope |
| F-05 | Tests that grant a permission and then reuse the same Python user object see the old grants: `test_parity_child_collection` (8 cases, `test_guardian_child_link_visibility.py:615`) and `test_guardian_child_object_state_once_after_parent_and_object_policy` (`tests/test1/test_cancel_permissions.py:637`). This is the lifetime cost of section 7. The tests re-fetch the user after the grant; the expected results stay. | expected, test shape | 7 |
| F-06 | `test_resolved_objects_and_checker_belong_to_one_request` (4 cases, `tests/test1/test_ancestor_boundaries.py:550, 554`) reads `_cv_guardian_ancestor_checker`, which 12.3 replaces. Its intent, that nothing about access is shared between two requests, is restated on the user object: two requests have two users and two checkers. | expected | 12.3 scope |
| F-07 | Three passages describe fresh or view-local checkers and are rewritten: `docs/reference/navbar.md:346` ("Guardian admission creates fresh checkers"), `docs/reference/context_buttons.md:245` ("no rendering-view argument to reuse a request-local Guardian checker"), and the module docstring of `src/crud_views_guardian/lib/ancestors.py`. | documentation | 12.3 scope |
| F-08 | Line drift: stage 1 removed two lines from `crud_views_guardian/lib/mixins.py`, so the checker sites 12.3 gives as `mixins.py:156, 213` are at 153 and 210. `ancestors.py:67, 70` are unchanged. | drift | 12.3 scope |

Decided by the maintainer on 2026-11-24. Like the decisions in 12.1 and 12.6, they are settled input and are not
under review (section 13, point 1).

| # | Decision | Amends |
|---|---|---|
| D-37 | A second check of the same object in one request uses the grants that request already loaded. A grant changed during a request is seen from the next request on. The workflow reload after a refused transition therefore shows the form with the error once more; the next request answers 403. No fresh checker, flag or bypass is added for it. This is the one stated exception to "every access decision is unchanged" in 12.3. | 12.3 constraints, D-02 |
| D-38 | `prefetch_perms` is not part of stage 2. Stage 2 adds a pinned query count for a Guardian list page with row actions, before and after the shared checker. Whether the grants of all rows of a list or card page are loaded in one step is decided afterwards on that measured figure, as its own change. | 7, 12.3 to verify |

Consequences the plan must carry:

- **Test:** only the `permission` case of the F-02 test is rewritten, to expect the rendered form with the error.
  The `scope` and `action` cases and the assertions on the scoped reload stay as they are.
- **Reasons, for the documentation of the lifetime (12.3):** nothing is protected by the second check, because the
  actor passed the gate in this request and the write was refused. The model-permission path already behaves this
  way: with `cv_guardian_accept_global_perms`, `user.has_perm` answers from Django's permission set on the user
  object. D-37 makes object grants consistent with it.
- **Limit of the evidence:** the probe found no other place that checks the same object twice in one request. That
  is as good as the test coverage; delete and bulk were not audited by reading. If the plan finds another such
  place, D-37 applies to it as well, and the plan names it.

- **D-38, why:** `get_objects_for_user` neither reads nor fills a checker (see below), so the row grants are not
  loaded when the row actions are checked. Each row action calls `cv_has_access(user, row)`. From reading the code,
  not measured: grant queries are paid per row and per action today, per row with the shared checker, and about two
  per page with `prefetch_perms`. No existing cost test pins a Guardian list page with row actions; the probe
  changed none.
- **D-38, why not now:** stage 2 replaces construction sites only. Prefetching needs a new call in the list and
  card rendering path where the page's rows are known, which changes a proven path. Guardian's `prefetch_perms`
  derives one model and content type from the objects it is given, so a polymorphic list with mixed models needs
  its own look.

Verified by the probe:

- The stage-1 decision matrix (`tests/test1/test_link_access_matrix.py` with `link_access_matrix_baseline.json`) and
  the access-trace suites pass unchanged. Apart from F-02 (D-37), no access decision changed.
- An attribute set on `request.user` survives Django's lazy user wrapper: every client-driven test outside the
  findings above passes.

Verified by reading the package and the installed django-guardian 3.5.2, not by a test:

- **Anonymous user.** The ancestor gate and the request gate deny an anonymous user before any checker is built.
  Only a direct `cv_has_access(user, obj)` call reaches the checker with an `AnonymousUser`. Guardian accepts it
  and maps it to its anonymous database user in the constructor, with one query per construction, which the shared
  checker also saves. Django creates a new `AnonymousUser` per request, so the attribute does not pass from one
  request to the next. The plan adds one test for this case.
- **`get_objects_for_user` list filtering** (section 11). Guardian's shortcut runs its own query and neither reads
  nor fills an `ObjectPermissionChecker`. List filtering stays a fresh query per request and is unchanged by
  stage 2.

Nothing in section 12.3 or 12.7 is left open or to verify.

### 12.8 Stage 3 amendments (2026-11-24)

Stage 3 was first written up as one issue, #411, with nine decisions S3-01 to S3-09 accepted by the maintainer.
A review of #411 against the code at `e444bbfc` found three points that were undecided or contradicted each other
(S3-08, the source of Cancel's parent, and a side effect of removing the Guardian list-page rewrite), and that the
issue carried nine behaviour changes, a public function, nine consumer migrations and five helper removals at once.
Two rounds of independent review of the replacement drafts raised further points. Each decision below that
does not come unchanged from #411 is marked "review".

The maintainer decided the following on 2026-11-24. The decisions replace #411 as planning input. #411 is closed
as superseded and its body is left as it was; the "From" column says where each decision comes from. Like the
decisions in 12.1, 12.6 and 12.7, they are settled input and are not under review (section 13, point 1).

Line references in this section are `feature/link-access-check-design` @ `e444bbfc`, with package paths
relative to `src/`. "Today" in this section means that code.

Terms used below:

- **Guard state:** the ancestors the request's ancestor guard resolved, kept on the view as `_cv_ancestor_state`.
- **Class step:** `_cv_link_permission`, the per-class part of the check's permission step.
- **The seam:** `_cv_page_link_ancestors`, by which a target class supplies its own ancestor list.
- **The rewrite:** the key-based overwrite in `GuardianQuerysetMixin.cv_get_context` (L1, D-34).
- **The state adapters:** `_cv_action_enabled_for_context` and `_cv_action_enabled_for_rendering`. With the removed
  `_cv_child_link_has_access` they are the "three private adapters" of 12.4 and 12.5.
- **Actor rule:** the requirement that the user is signed in and active.

**Delivery**

| # | Decision | From |
|---|---|---|
| D-39 | Stage 3 is delivered as three issues, in this order: 3a moves the consumers to the check, 3b removes the Guardian exceptions, 3c publishes the function. All three are in milestone 1.0.0. Their pull requests target `feature/link-access-check-design`, as #409 and #410 did; the stage issues close when that branch is merged to `main`. | review |

**Stage 3a: consumers moved to the check**

| # | Decision | From | Amends |
|---|---|---|---|
| D-40 | Every package call site moves to the check for every target, Guardian targets included: the four context button classes, actions by view key, card actions, navbar items, the `cv_context_has_permission` filter, core Cancel and the bulk toolbar. Each site hands its rendering view to the private function when that view belongs to the target's own ViewSet, and `None` otherwise, so `cv_create_has_access` only ever receives a view of its own ViewSet. This departs from S3-06, which handed the view over everywhere. A Guardian object or list target therefore gains the parent and higher-ancestor gates the request already runs. Guardian's own exceptions (D-30, D-33 with D-27, D-34, D-35 and the nested Guardian Cancel path) stay until 3b, except as the consequences below state. | review | D-28, D-29, D-31 |
| D-41 | D-04 is completed. A consumer hands the check the immediate parent and every higher ancestor the request has already resolved, nearest first and aligned with the target's declared ancestry. A level that is not known is `None` and is not gated; it never shifts a farther object into its place. Nothing is loaded to decide a link. For a target on the page's own ViewSet the immediate parent comes from the guard state, not from `cv_get_parent_object`; for a child link it is the object or row its URL is built from. Cancel alone uses the hook (D-42). A nested target whose immediate parent is not known is denied at every consumer, also on a view that did not run the ancestor guard. | #411, review | D-13, D-26, D-36 |
| D-42 | Cancel takes its immediate parent from `cv_get_parent_object`, as today, through the existing `_cv_cancel_parent_object`, which treats a 404 of the built-in lookup as "unavailable". On a guarded request that is the resolved parent, without a query. A project override of the hook keeps working. On a view that did not run the guard the hook's existing lookup still finds the parent, so Cancel is the one consumer that does not deny there. Higher ancestors for Cancel come from the guard state only. | review | D-41 |
| D-43 | The bulk toolbar is a link to a view of the same ViewSet and calls the check directly, like a context button. It no longer goes through the cancel helper. | review | 9 |
| D-44 | `cv_context_has_permission` stays permission-only. It runs the parent gates and the own permission and never the state hook, so it can answer true for an action that is disabled by state. | #411 (S3-02) | 9 |
| D-55 | The immediate-parent-only handling of a nested Guardian create that 3a keeps is bound to the two mechanisms that produce it, the seam and the rewrite, not to the page. A navbar child item uses neither and always receives the aligned list, also when the navbar renders on a page of the create's own ViewSet. Decided while #412 was planned, after a probe showed both outcomes. | planning of #412 | D-40 |
| D-52 | Bulk return redirects (GET, the warning POST and the Cancel button of the all-blocked page) follow Cancel's eligibility as changed by 3a and 3b. The order origin, fallback, success URL stays. The chosen `Location` may change; authorization responses and login redirects do not. This applies in 3a and again in 3b. | #411 (S3-09) | none |

**Stage 3b: Guardian exceptions removed**

| # | Decision | From | Amends |
|---|---|---|---|
| D-45 | The kept denials for a nested Guardian create end wherever the route's parent is known: the sibling button, the create control on the create page, the permission filter on a child list page and the `ManyToMany` child page. A parent is never guessed from a relation. | #411 (S3-01) | D-27, D-33 |
| D-46 | A link to any nested Guardian view requires a signed-in, active user, under protected and unprotected ancestry alike. That is the request's rule and the rule a nested Guardian list link already has; it is extended to the nested create and to nested object views. The rule runs before `cv_create_has_access`, so an override cannot admit an anonymous user. L2 ends: an anonymous backend grant under a model-permission parent no longer shows the create link, and neither does a parent with provider `none`. A direct call to the default `cv_create_has_access` of a nested create answers the same. Top-level Guardian links keep their rules. This goes beyond S3-03, which kept the unprotected case. | #411 (S3-03), review | D-18, D-35, 5.4 |
| D-47 | A queryset-only Guardian composition also checks its declared parent policy, for links and for Cancel to that list. Own permission and the filtering of list rows are unchanged. | #411 (S3-04) | D-30 |
| D-48 | Nested Guardian Cancel moves onto the check for object, list and create targets, with the higher ancestors. Guardian Cancel targets keep their actor rule and the composition validation around the check. The actor rule is not loosened to the rule of an ordinary top-level Guardian list link. | #411 (S3-05), review | none |
| D-49 | For a nested Guardian create the declared parent gates run first, at every consumer. `cv_create_has_access` is asked only when they pass; an override that answers true cannot restore a link the gates denied, and an override that answers false still denies. Cancel already works this way. No bypass flag is added to spare the default hook its second look at the parent. | #411 (S3-07) | D-28, D-32 |
| D-50 | L1 ends. `GuardianQuerysetMixin.cv_get_context` no longer rewrites a button's result by key; each button is decided once for its actual target. | #411 | D-34 |
| D-51 | S3-08 is not adopted. It would have made an ordinary link to a parent-only Guardian view stop asking the child model permission while still honouring an "explicit" custom denial. A nested Guardian view that is parent-only and not a create keeps today's two behaviours: an ordinary link asks its inherited `cv_has_access`, which requires the child model permission the request does not require, and Cancel does not ask `cv_has_access` at all. The first is a documented known limit: a link can be hidden that the request would allow. No detection of "explicit" against "inherited" overrides is built. It is decided again when a project reports the case. Cancel keeps its own branch for this shape, because the check would ask the child model permission. In 3b that branch gains the higher-ancestor gates; not asking `cv_has_access` is then its one difference from the check. | review | 5.6 |

**Stage 3c: the public function**

| # | Decision | From | Amends |
|---|---|---|---|
| D-53 | `check_link_access` is published in 1.0 as a standalone function, stable, after 3a and 3b. Its inputs are the target view class, the user, the target's own object and the known ancestors. It answers allowed, denied by permission or denied by state. It takes no rendering view and passes `None` to `cv_create_has_access`; package consumers hand the real view to the private function (D-40). The permission-only function stays private. No accessor for the ancestors a request resolved is published; a project caller supplies what it has, and a level it does not supply is unchecked. No provisional status is introduced. | #411 (S3-06), review | D-17, 9 |
| D-54 | The public function validates its inputs before it decides anything and raises `ImproperlyConfigured` when they do not fit the target: an ancestor that is not of the model of its level in the target's declared ancestry; an own object that is not of the target's model; no own object for an object target; an own object for a target without one; more ancestors than the target has levels; any ancestor for a top-level target. An object fits a level when it is an instance of that level's concrete model, so a proxy, a multi-table child and a polymorphic subclass pass; for a Resource target the own object is an instance of the Resource class. Every element counts towards the length, `None` included. A list shorter than the ancestry and `None` for a higher level stay allowed and mean "not known". The private function and its package callers are not changed by this. | review | 5.1 |

Consequences the plans must carry. They follow from the decisions and from reading the code; they are not decisions.

- **D-40, direction of change:** the check is built from the request gate's pieces, so a Guardian link that 3a
  newly hides is one whose click the request refuses. This follows from reading the code. The stage-1 matrix has
  not been run against it; 3a records every changed cell with its reason.
- **D-40, the create seam:** `_cv_page_link_ancestors` survives 3a with one override, on the Guardian create view
  (`crud_views_guardian/lib/views.py:282-293`). It is what keeps D-27 and D-33 until 3b removes it. Its core
  default changes meaning from "use the page's own code path" to "use the aligned list of D-41".
- **D-40, the state adapters:** after 3a the only production caller of `_cv_action_enabled_for_rendering` is the
  nested Guardian Cancel path (`crud_views_guardian/lib/mixins.py:435`), which 3a does not touch. The adapters, the
  core create view's overrides of them (`crud_views/lib/views/create.py:36-75`) included, are removed in 3b. Tests
  call or override them by name: `tests/test1/test_ancestor_resolution.py:749, 771`,
  `test_ancestor_helpers.py:289`, `test_guardian_parent_none.py:452, 629, 936`,
  `test_core_nested_create_state.py:128, 180, 232` and `test_cancel_permissions.py:306, 474, 497-499`;
  `test_link_access.py:535-562` calls the seam by name. This list is a starting point, not complete; 3b rewrites
  and lists every such line, as D-25 did for stage 1. 3a already has to rewrite the tests that observe a migrated
  consumer through the rendering adapter (`test_navbar_checks.py`, `test_navbar_templates.py`,
  `test_navbar_costs.py`, `test_cancel_state.py`, `test_cancel_permissions.py`, `test_bulk_source.py`) and the two
  lines of `test_link_access.py` that name `_page_action_object`.
- **D-40, where a Guardian target does not yet gain a gate:** a nested Guardian create is handed the immediate
  parent only, and gets no higher-ancestor gate until 3b, where a site consults the seam (context buttons, actions
  by view key, card own actions and the permission filter, on the pages of the create's own ViewSet, and a parent
  button on a page one level below, `crud_views/lib/view/buttons.py:183`) or where the rewrite applies. With the
  parent button a higher ancestor exists only from four levels on. A child button, a card child action and a navbar
  child item hand over the aligned list, so there it gains the higher-ancestor gates in 3a. A navbar child item
  does so on every page that renders the navbar, the pages of the create's own ViewSet included (D-55); on such a
  page the navbar item and the context create button can differ until 3b. A queryset-only composition keeps
  skipping the immediate parent (D-30), but the higher-ancestor gates run before that class step
  (`crud_views/lib/link_access.py:74`), so on three or more levels D-30 is partly ended in 3a. Cancel to a
  queryset-only nested list defers to the core check (`mixins.py:252-256`) and gains the higher-ancestor gates in
  3a as well.
- **D-40, the rendering view:** today the hook receives a view from the create button of the nested list or card
  page, through the rewrite (`mixins.py:330`), and from Cancel (`mixins.py:442`), both of its own ViewSet. It
  receives `None` everywhere else, the own ViewSet's object pages and its row and card actions included. Under D-40
  those sites hand their view over too; pages of other ViewSets keep handing `None`. The list page still hands over
  the list view after 3b removes the rewrite. An override that calls `rendering_view.cv_get_parent_object()`
  therefore always gets its own parent.
- **D-41, the hook and the buttons:** today a core nested create button takes its state object, and the parent
  button its object, from `cv_get_parent_object` (`crud_views/lib/views/create.py:63-64`,
  `crud_views/lib/view/buttons.py:177-181`). From 3a on they use the guard state. A project override of the hook no
  longer reaches them; a project that annotates the parent does it in the parent ViewSet's queryset, which the
  guard uses.
- **D-40 with D-48:** nested Guardian Cancel keeps its own path through 3a (`mixins.py:414-435`), which gates the
  immediate parent only. It gains the higher ancestors in 3b. Between the two, a nested Guardian button and the
  Cancel link to the same view can differ on a higher ancestor.
- **D-41 with D-35:** the higher-ancestor gates deny an anonymous or inactive actor as soon as one higher level is
  gated (`crud_views/lib/link_access.py:53-54`). A child link to a nested Guardian create below a gated higher
  ancestor is therefore denied for an anonymous actor from 3a on. L2 remains where no higher level is gated, until
  D-46.
- **D-41, views without guard state:** a nested list or object view that has a request but no guard state raises
  before it renders (`crud_views/lib/ancestors.py:598-605`). The shapes that reach a link decision without guard
  state are create and form pages, Resource leaves, non-CRUD views and direct calls.
- **D-42:** the hook and its lookup exist today (`crud_views/lib/view/base.py:1005-1017, 1198-1217`). One call is
  new: Cancel to a nested object target did not ask for the parent (`base.py:82-83`) and now does. On a guarded
  request that costs no query. On a view without guard state it is one lookup, and an exception raised by a project
  override of the hook now reaches this path. No test pins a project override here; 3a adds one.
- **D-43:** the documented Guardian bulk view subclasses the core bulk view and carries no Guardian mixin
  (`docs/reference/bulk_actions.md`, "With Guardian"), so the Guardian Cancel overrides never applied to it.
- **D-40 with D-19:** permission before state is D-19. It changes the three button classes, actions by view key and
  the card own action; Cancel, the bulk toolbar and navbar owner items already follow it. With the second branch
  gone from each call site, `_page_action_object` has no caller and is removed in 3a.
- **D-40, configuration errors:** a missing ancestor permission key, a view without operation requirements and
  authorization records on another database are raised when the link is decided. A missing own permission key
  denies, as today.
- **D-45, the own child:** `cv_create_has_access` keeps accepting an own child of a single-foreign-key nesting and
  resolving its parent (`crud_views_guardian/lib/views.py:311-317`). That is the hook's documented input, not a
  parent guessed to decide a link.
- **D-46, who can see a difference:** probed at `e444bbfc` under a provider-`none` parent, with Guardian's
  anonymous user holding `view` on one child: the link check answers allowed for the nested detail and for the
  nested create, denied for the nested list, and the detail request answers with the login redirect. Pages built
  from the shipped Guardian view classes refuse an anonymous user themselves, so no such page changes. A ViewSet
  that mixes in a plain view without a permission mixin under fully unprotected ancestry admits everybody, and no
  system check forbids that mix; on such a page the link disappears. That last part is from reading.
- **D-45 with D-50:** the rewrite is also what gives the plain create button on a nested Guardian list or card page
  its parent, because the seam answers `()` for a page without an object
  (`crud_views_guardian/lib/views.py:287-291`). The two decisions land in one change; the rewrite is not removed
  first. With them the create control gains the higher-ancestor gates on every page of its own ViewSet.
- **Order inside 3b:** D-49 lands with or before the move of Cancel onto the check (D-48); otherwise an override
  that answers true restores a Cancel link, because the create's class step is the hook alone (`views.py:387`).
  D-46 lands with or before D-45, so that no newly shown create link is shown to an anonymous user. The adapters go
  after the Cancel move. 3b is one pull request; these are constraints on its commits.
- **D-50:** the rewrite applies to a button of any class on a nested page (`mixins.py:313-330`). A project
  `ContextButton` subclass with its own `get_context` that links to a nested Guardian create is corrected by it
  today and is hidden once it is gone. The migration note names this and points to `cv_create_has_access`; 3c
  changes the pointer to `check_link_access`.
- **D-51:** the child model permission is asked only by a view built on a `...PermissionRequired` base; on a plain
  `CrudView` base `cv_has_access` answers true. The ordinary link to this shape gains the parent and
  higher-ancestor gates in 3a like any other target. What remains of `_cv_cancel_parent_target_access`
  (`mixins.py:438-443`) after 3b is listed as a retained helper with this reason. The only view of this shape found
  in the repository is a test fixture (`tests/test1/test_cancel_permissions.py:462`).
- **D-53:** a project override of `cv_create_has_access` that reads the rendering view can answer differently for a
  project call than for a package button on the same page. The reference says so. Without the view the default hook
  only loses the swap of an equal parent for the request's own instance (`crud_views/lib/ancestors.py:676-679`);
  its answer is the same. A rendering-view argument can be added later without a breaking change. What is frozen is
  the representation of the three outcomes.
- **D-53, what a project caller cannot match:** on a CRUD page a project has `cv_get_parent_object` and nothing
  public for the levels above. A custom button therefore differs from a package button where the target asks a
  stricter higher-level permission than the page; with the default policies it does not. The function also does not
  check membership: it accepts a child with another parent than its own, where the request answers 404.
- **D-54, same exception type:** the gates raise `ImproperlyConfigured` for configuration errors as well, so a
  caller cannot tell the two apart by type. The validation messages start with the function's name. Counting levels
  walks the declared ancestry, so a broken ancestry is reported during validation, with its own message. No new
  exception class is added.
- **D-54:** a model-permission parent ignores the object (`crud_views/lib/viewset/__init__.py:507-509`), so without
  the check any object would count as a known parent, and the project's state hook would receive it. A parent
  ViewSet is never a Resource (system check `viewset.E261`), so every ancestor level has a model.

Carried over from #411 without change, as constraints on all three issues: the request gate, its responses, its
trace and the published `cv_access` / `cv_manage_view` formats are unchanged; configuration errors are raised, not
turned into hidden links; only grants are shared and no decision is stored; no ancestor is loaded to decide a
link; breadcrumb and site menu are not built; `prefetch_perms`, `force_full_hierarchy_check` and a cross-request
cache stay out.

No decision in section 12.8 is open. What each issue leaves to its planner is listed in the issue.

## 13. Reviewer brief

For external reviewers of a plan or of code that implements a stage of this concept.

1. **The concept is fixed input.** Sections 1 to 12 record decisions the maintainer has taken. They are not under
   review. Do not propose a different architecture, a more general mechanism, or a broader scope.
2. **Only defects count.** Report a finding only when you can name a concrete case, for example:
   - a link or button that is shown without the parent check the request would apply;
   - a direct call to a public hook that now answers "allowed" where it answered "denied" before;
   - a call site that the change missed, with file and line;
   - a project override that changes behaviour without a migration note;
   - a difference in the request gate's order, response or trace output;
   - a state or business rule that can end up in a cache.
3. **Design alternatives are out of scope** unless you show that the plan or code violates one of the anti-goals in
   section 2. In that case name the anti-goal and the case.
4. **Give evidence.** Each finding states the input, what happens, and what should happen. Mark anything you did
   not verify against the source as unverified.
5. **Report independently.** Do not respond to other reviewers. The maintainer sorts all reports once into "fix",
   "document" and "ignore".
