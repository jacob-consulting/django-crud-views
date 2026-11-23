# Concept: one link access check, shared grants, and what is deliberately left out

Date: 2026-11-23. Status: concept approved by the maintainer on 2026-11-23; **no implementation is authorized by this
document**. It is not an implementation plan. Each stage in section 9 needs its own issue, plan and approval.

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

### 12.4 Open for the planner

These are the planner's to decide, within the decisions above:

- Name, module and exact signature of the check.
- How step 2 is satisfied for a view whose only rule is the parent rule (the nested Guardian create).
- Which of the three private adapters can be removed in stage 1 and which must wait for stage 3.
- The exact wording and extent of the Breaking entry.
- The remaining items of section 11.

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
