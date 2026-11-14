# Design: access trace for django-crud-views (`cv_access` and the manage page form)

**Date:** 2026-11-14
**Status:** approved by the maintainer. Upstream issue:
[django-crud-views#370](https://github.com/jacob-consulting/django-crud-views/issues/370).
**Mockup:** [`2026-11-14-access-trace-mockup.html`](2026-11-14-access-trace-mockup.html), next to this file: the Access
check card on the manage page and the command's output, with the tabler-test demo's data (self-contained apart
from Tabler 1.6.1 CSS from jsDelivr; open it in a browser).
**Depends on:** [#366](https://github.com/jacob-consulting/django-crud-views/issues/366) (structured manage page;
design in [`2026-11-14-manage-page-design.md`](2026-11-14-manage-page-design.md)). References such as "#366 D-27"
point at that design's decisions.
**Split off:** the configuration dump `cv_manage_view` is
[#371](https://github.com/jacob-consulting/django-crud-views/issues/371) and not part of this design.
**Origin:** written in the tabler-test demo project; the mockup uses that demo's data.
**Code references:** commit `4510cee9`, paths relative to `src/`.
**Layout:** this file is written to be copied into #370 as its body: Summary, Problem, gsd-handover, Acceptance
criteria.

## Summary

Add one **access trace**: given a URL path and a user, it runs the library's real authorization code and reports
every check in order, what it required, where that rule comes from, and which check decided the outcome. Two front
ends show the result:

- a management command, `cv_access <path> <user>`;
- a form on the manage page, switched on per project by a setting.

It answers "can this user open this, and why or why not" without signing in as that user.

## Problem

Downstream projects will need to explain access against real production data: a user reports "I can't open X", or
someone asks "why can Y see this?". The answer depends on that user's grants and on the objects along the URL, and
today nothing reports it.

- **The only tool is signing in as the user.** The docs describe it: add the user to the manage group, sign in as
  them, read the manage page, remove the membership (`docs/reference/settings.md`, "Diagnose the signed-in
  account").
- **The manage page shows configuration, not a result.** #366 adds one "Access for: you" row for the signed-in user
  at model level (#366 D-05). It can't say whether a user reaches one object, or which ancestor refused a nested
  request.
- **A denial carries no reason.** The ancestor engine stops at the first failing gate with a bare
  `PermissionDenied` (`crud_views/lib/ancestors.py:483-484`). Nothing records the steps that passed or which
  permission was asked.
- **The checks are spread over several places.** There is no single function that is "the authorization path":
  - the ancestors: `_authorize_ancestors(view)` (`crud_views/lib/ancestors.py:452-488`);
  - model permission and action state: `has_permission()` (`crud_views/lib/view/base.py:1204-1219`);
  - the Guardian object grant: `get_object()` (`crud_views_guardian/lib/mixins.py:117-127`);
  - the Guardian list filter: `get_queryset()` (`crud_views_guardian/lib/mixins.py`, `GuardianQuerysetMixin`);
  - the manage gate: `ManageView._cv_manage_allowed()` (`crud_views/lib/views/manage.py:39-51`).

What the code already offers:

- **The real engine can run without a web request.** `_authorize_ancestors` needs only a view instance with a
  user and the URL's pks (`view.request.user`, `view.kwargs`). Django builds such an instance from a path with
  `resolve()` and `View.setup()`, without calling a handler.
- **The plan of ancestor gates is computable without the database:** which ancestors are gated, with which half of
  the permission pair, and where the pair comes from (`_requirement_source`, `_selected_gates`,
  `crud_views/lib/ancestors.py:345-404`).
- **Read or write is decided by the view's class,** never by the HTTP method (`_operation_family`,
  `crud_views/lib/ancestors.py:243-252`), and no gate reads the query string.

## gsd-handover

Carry these decisions into GSD planning without reopening them absent a concrete conflict. They were made in a
design session on 2026-11-14 against the code at `4510cee9`. Decision numbers D-01 to D-23 are grouped by topic,
not in numeric order.

### Goals, non-goals, anti-goals

**Goals:**
- A developer learns the outcome for one user and one URL, and the first check that decided it.
- The explanation comes from the code that enforces access, not from a description of it.
- It works on a server shell and, where a project allows it, in the browser on production.

**Non-goals:**
- **No impersonation.** Nobody is signed in as another user, and no session is created for them.
- **No change to who may open what.** No gate's behaviour changes when no trace is running.
- **No configuration dump.** Printing the manage page's content on the command line is #371.
- **No trace of what a page renders.** Which buttons or rows a page shows is out of scope, except the row count of
  a Guardian list (D-07).
- **No manage page for Resource ViewSets.** That is
  [#372](https://github.com/jacob-consulting/django-crud-views/issues/372). The command and the path field cover
  Resource URLs already; the per-ViewSet form (D-14) reaches them once #372 exists.
- **No bulk mode.** One user and one path per run; the page form's per-view table (D-14) is the only multiple.

**Anti-goals (failure even if it works):**
- **A second implementation of the checks** that can drift from the enforced ones.
- **A side effect:** a trace that writes to the database or runs a view's handler.
- **A trace that changes an outcome:** a request that is allowed without a recorder and denied with one, or the
  reverse.
- **Access to other users' results on the web by default.**

### Approaches considered

How the trace gets its steps:

1. **A recorder inside the real engine.** The ancestor engine and the library's gates take an optional recorder and
   note each step. With no recorder, nothing changes.
   - Faithful by construction: one code path.
   - Adds a few lines to security code.
   - A project's overridden gate shows as one opaque step.
   - **Chosen.**
2. **A second driver outside the engine.** A trace module calls the engine's building blocks in the same order.
   - Security code stays untouched.
   - The order of steps is written twice (`crud_views/lib/ancestors.py:472-487`), and the copy drifts exactly when
     someone is debugging.
   - **Rejected.**
3. **Black box plus plan.** The engine runs unchanged and yields only the outcome; the plan is printed next to it,
   and on a denial the gates are probed one by one.
   - Least work, and the outcome is always the real one.
   - The explanation is partly inferred.
   - **Rejected.**

Where it is used:

- **Command only.** Rejected: many deployments have no shell access for the developers who answer these questions.
- **Page form only.** Rejected: no use in scripts, and the web exposure would be the only way in.
- **Both, from one trace function, command first.** Chosen. One downstream project has shell access through
  Kubernetes; others have only the browser.

### Approved decisions

#### The trace

- **D-01 — One trace function.**
  - Input: a URL path and a user (or the anonymous user). Nothing else: the HTTP method and the query string play
    no part in authorization (see Problem).
  - Output: a trace object with the ordered steps and the outcome (D-05, D-06).
  - The command and the page form both call it and only format its result.
  - It lives in the core package and has no dependency on Guardian; Guardian's gates report through the same
    recorder (D-02).
- **D-02 — A recorder inside the real code.**
  - `_authorize_ancestors` and the library's own gates accept an optional recorder and report each step to it:
    - the ancestor engine: static validation, actor admission, each ancestor lookup, each gate
      (`crud_views/lib/ancestors.py:452-488`);
    - the model-permission and action-state gate (`crud_views/lib/view/base.py:1204-1219`);
    - the Guardian object gate and list filter (`crud_views_guardian/lib/mixins.py:117-127` and
      `GuardianQuerysetMixin.get_queryset`);
    - the Guardian parent mixin's composition check and state gate
      (`crud_views_guardian/lib/mixins.py:387-400`);
    - the Guardian ancestor gate (`GuardianViewSet._ancestor_has_permission`,
      `crud_views_guardian/lib/viewset.py:83-91`);
    - the manage gate (`crud_views/lib/views/manage.py:39-51`).
  - The recorder reaches those places through a context variable. The public signatures of `has_permission()`,
    `get_object()` and `cv_has_access()` don't change, and a recorder can be switched on from outside a view
    (D-19).
  - A step reported twice in one run is recorded once. `get_object()` runs twice for a permission-required object
    view: in the state gate (`crud_views/lib/view/base.py:1218`) and in the stub (D-03).
  - **With no recorder, behaviour is unchanged.** A recorder only observes; it never decides and never ends a run.
- **D-03 — The view's real `dispatch()` runs, with a stub handler.**
  - The trace resolves the path, builds the view instance as Django does (`resolve()`, the view class and its
    init kwargs, `View.setup()` with a synthetic request whose `user` is the traced user), and calls the instance's
    `dispatch()`.
  - Before that, it replaces the HTTP handler on the instance (`get`) with a stub. The stub loads what the real
    handler would load to reach the remaining gates, and nothing more:
    - an object view: `get_object()`, which holds the Guardian object gate;
    - a list view: the queryset, counted (D-07);
    - any other view: nothing.
  - The whole dispatch chain therefore runs, project mixins included, in the project's own order; the real handler
    never runs.
  - The synthetic request is a GET. It carries a throwaway session that is never saved and a throwaway message
    store, because project gates may expect both on a request.
  - Rejected: calling the gates one by one from the trace. That is approach 2 again for the local gates.
- **D-04 — The plan is shown next to what ran.**
  - For a nested request the trace first lists the planned ancestor gates from the existing pure functions
    (`_validate_ancestor_structure`, `_requirement_source`, `_selected_gates`): each gated ancestor, the permission
    key, and the rule's source label (e.g. `actions['publish']`, `ancestor_policy.write`,
    `global CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS`).
  - The engine stops at the first denial, so later gates never run. They appear as "not reached", taken from the
    plan.
  - The view's own requirement comes from the requirement method of #366 D-27.
- **D-05 — What a step records.**
  - its kind: route, validation, actor admission, ancestor lookup, ancestor gate, own permission, object grant,
    list filter, action state, manage gate, custom gate;
  - what it concerned: the ViewSet, and the object's model and pk where there is one;
  - what it required: the full permission string (`sales.change_customer`) or the group, the provider (`model`,
    `guardian`, `none`), and the source of the rule;
  - the result: passed, denied, not found, skipped, not reached, or error with the message;
  - for a passed Guardian gate, how it passed: object grant, model permission through the fallback, or active
    superuser.
  - No object content is recorded, only model and pk.
- **D-06 — Outcomes.** One of:
  - **allowed**;
  - **denied** (the request would answer 403), with the first denying step;
  - **not found** (404), with the lookup that missed;
  - **login redirect**, for an anonymous user where the endpoint redirects;
  - **error**, when the code raises anything other than a 403 or 404, with the exception's class and message.
    This covers `ImproperlyConfigured` (e.g. a nested endpoint without its `actions` entry, or authorization
    records on another database than `default`), the `AssertionError` core raises for a permission key missing
    from the map (`crud_views/lib/view/base.py:1167`), and whatever a project gate raises;
  - **no such route**, when the path resolves to nothing, or to a view that is not a `CrudView`.
- **D-22 — "Allowed" means "may open the page"; the trace says what it didn't check.**
  - The trace covers every check a view performs before its handler. Two kinds of refusal happen later, inside the
    handler, and are not evaluated:
    - **per user, on submit:** a workflow view checks the permission for the chosen transition only in its form and
      POST (`crud_views_workflow/lib/views.py:76-110`);
    - **configuration, when the page is built or submitted:** the database checks of a nested list
      (`crud_views/lib/view/base.py:265-279`), the delete preview (`crud_views/lib/views/delete.py:315-321`) and
      writes (`crud_views/lib/views/mixins.py:44`, `crud_views/lib/views/action.py:19`,
      `crud_views_workflow/lib/views.py:90`).
  - Where one of these applies, the trace adds a step with the result **not evaluated** and the reason, e.g.
    "transition permissions are checked on submit" or "database configuration is checked when the page is built".
  - The text output's final line says "may open the page", not only "allowed".
  - Rejected:
    - the stub calling the real `get_context_data()`: it would catch the list and delete cases with real code, but
      a trace would build tables and delete previews, and submit-time rules stay uncovered;
    - the workflow package reporting which transitions the user may perform: it closes the one per-user gap, at
      the cost of trace code in a third package. It can be added later.
- **D-23 — Checks outside the view: only Django's login middleware.**
  - The trace calls the view directly, so the project's middleware and decorators in the URL configuration don't
    run.
  - When `django.contrib.auth.middleware.LoginRequiredMiddleware` or a subclass is in `MIDDLEWARE`, the trace calls
    that middleware's real `process_view()` with the resolved view as its first step and records the result. No
    rule is copied. This matters for the anonymous user: a plain view has nothing else that stops them, and the
    real request is redirected to login.
  - Every trace carries one fixed line: "other middleware and URL decorators are not traced". The docs repeat it.
  - Rejected:
    - running the whole middleware chain: middleware opens sessions, writes logs and has other side effects,
      which breaks D-09;
    - documenting the gap only: the trace would be wrong for the anonymous user in a common setup.
- **D-07 — A Guardian list reports its filter.** Opening a Guardian list is always allowed; the filter is the real
  answer. The trace reports "allowed, sees n of m objects": n from the view's filtered queryset, m from the
  queryset just before the Guardian filter is applied inside `GuardianQuerysetMixin.get_queryset`
  (`crud_views_guardian/lib/mixins.py:276-291`), so a project's own `get_queryset` override is included in both.
  The two counts are taken in the stub (D-03), so a real request never pays for them.
- **D-08 — A project's own gate is one opaque step.** When a project view overrides `has_permission()`,
  `get_object()` or `dispatch()` and denies without passing through a library gate, the trace shows a "custom gate"
  step with the method's name, its class and the result. The recorder can't see inside project code.
- **D-09 — Read-only by a rolled-back transaction.**
  - The trace runs inside `transaction.atomic()` on the default database and always rolls back, on the command line
    and inside the page's request (a savepoint there).
  - A project hook that writes during a gate therefore leaves nothing behind.
  - The trace sends no messages (`django.contrib.messages`) and saves no session.
  - This covers the database. A project gate that calls an external service is the project's own code and outside
    the guarantee; the docs say so.
  - Process-wide caches filled during a trace (content types, the permission map) are not undone. That is the
    same as for any request.
- **D-10 — Resource views are traced like any other.**
  - Resource ViewSets follow the same ancestor authorization and permission checks, so the trace runs the same
    way. The application's loader runs as in a real request: `cv_get_item()` for an object view, reached through
    the state gate (`crud_views/lib/view/base.py:1218`, `crud_views/lib/resource.py:162-166`), and
    `cv_get_items()` for a list.
  - The trace therefore reports a missing item as "not found" and includes the action state.
  - Why this is safe: the loaders only read (`crud_views/lib/resource.py:106-126`). Resources have no create,
    update or delete views; a write happens in an action view's handler, which never runs (D-03).
  - Consequence, stated in the docs: tracing a Resource URL may call the external source the loader reads, with
    the traced user on the request.
  - A Resource list reports its row count, not "n of m": there is no filter to compare against.
  - Rejected: halting before the item is loaded. It left the outcome undetermined, and it would have been the one
    place where a recorder changes what the code does.
- **D-11 — The traced user.**
  - Any user of the project's user model, by username or primary key, active or inactive, or the anonymous user.
  - An inactive user is traced like any other; the gates' own inactive rules decide (`_protected_actor_response`,
    `crud_views/lib/ancestors.py:417-425`; `_guardian_inactive_actor`).
  - The user object is loaded fresh for the trace, so no permission cache from another request is reused.

#### The command

- **D-12 — `cv_access <path> <user>`.**
  - `<path>` is a URL path of the project, e.g. `/customer/5/order/12/detail/`. A full URL is accepted and reduced
    to its path.
  - `<user>` is a username or a primary key. When a value matches one user's username and another's primary key,
    the username wins. `--anonymous` replaces it.
  - An unknown user or a path without a route ends with exit code 2 and a one-line message.
  - Rejected names: `cv_manage_url` (the issue's working name), which suggests the tool belongs to the manage page.
- **D-13 — Output and exit codes.**
  - **Text by default:** a header (path, route name, view class, user), the numbered steps, then the outcome and
    the deciding step.
  - **`--as-json`:** the same trace as one JSON document, with a `version` key so scripts can rely on the shape.
  - **Both are coloured:** passed green, denied red, not reached and skipped dimmed, errors yellow; in JSON, keys
    and the result values.
  - **`--no-color`** switches colour off. This is Django's own option on every management command, together with
    `--force-color`; `cv_access` uses them and adds no flag of its own. Django also leaves colour off when the
    output is not a terminal, so `cv_access … --as-json | jq` receives plain JSON.
  - No new dependency for colouring. Django's named style roles follow the user's `DJANGO_COLORS` and have no
    dimmed style, so the command defines its own fixed styles and applies them only when Django's colour handling
    is active.
  - **Exit codes:** 0 allowed; 1 denied, not found or login redirect; 2 wrong call, no such route or error.

  Text output, as a sketch:

  ```
  cv_access /customer/5/order/12/update/ sam

  path    /customer/5/order/12/update/
  route   order-update  →  sales.views.orders.OrderUpdateView
  user    sam (active)

  plan    customer  parent: change   guardian   ancestor_policy.write
  1  ✓  route resolved
  2  ✓  ancestor structure and declarations valid
  3  ✓  actor admitted (authenticated, active)
  4  ✓  customer 5 found
  5  ✗  customer 5: needs sales.change_customer (guardian, strict)   no object grant, no fallback
  6  ·  order 12: needs sales.change_order (own permission)          not reached
  7  ·  order 12: action state                                       not reached

  DENIED at step 5: sam has no change grant on customer 5.
  ```

#### The page form

- **D-14 — Two ways to ask, on the manage page.**
  - **For this ViewSet:** a typed username and an optional object pk. The page supplies the ViewSet and, on a
    nested manage page, the parent pks from its own URL. The result is:
    - the user's row in the permission matrix (#366 D-05), in place of "you";
    - one line per view: the outcome and the deciding step, expandable to the full trace. Without an object pk, an
      object view says "needs an object pk".
    - Every registered view is listed, POST-only and backend-only ones included; they have access checks too.
    - A view whose URL needs more than the parent pks and a pk says "use the path field". Shipped cases: the
      child redirect (`crud_views/lib/views/child.py:26-36`) and polymorphic create
      (`crud_views_polymorphic/lib/create.py:18-26`).
  - **For any URL:** a path field. The result is one full trace, as the command prints it.
  - Both sit in one card, "Access check", in the main column under the Permissions card.
  - The username is typed, never offered from a list. An unknown username says so.
  - It is a GET form and changes nothing. A result is linkable.
  - This replaces the sketch in #366 D-29, which had only the first way.

  As a sketch:

  ```
  Access check                                                    [?]
  ┌ this ViewSet ─────────────────────────────────────────────────┐
  │ user [sam        ]  object pk [7   ]  [Check]                 │
  └───────────────────────────────────────────────────────────────┘
  ┌ any URL ──────────────────────────────────────────────────────┐
  │ user [sam        ]  path [/customer/5/order/12/update/] [Check]│
  └───────────────────────────────────────────────────────────────┘

  sam · customer 7
  › list     allowed   sees 4 of 31 objects
  › detail   allowed   object grant view_customer
  › create   denied    needs sales.add_customer
  › update   allowed   object grant change_customer
  › delete   denied    needs sales.delete_customer
  › manage   denied    needs group CRUD_VIEWS_MANAGE
  ```

- **D-15 — Off by default, switched on by a setting.**
  - A new setting `CRUD_VIEWS_MANAGE_ACCESS_TRACE`, default `False`, read like the other manage settings
    (`crud_views/lib/settings.py:34-38`).
  - Off: the card is not rendered, and its GET parameters are ignored.
  - On: any user who may open the manage page may trace any user on any path. No further permission is asked, and
    the viewer does not have to pass the traced path's ancestor checks themselves.
  - Why a setting: #361 kept "check as user X" off the web deliberately, so each project decides for its own
    production. Why group membership then suffices: the developer who diagnoses usually holds no business
    permissions.
  - Accepted consequence: a trace reveals whether an object exists (not found versus denied) and whether another
    user reaches it, also under a parent the viewer can't open. It never shows the object's content (D-05).
  - The command is not affected by the setting. Shell access already means database access.
  - Rejected:
    - always on, with the viewer passing the same ancestor checks: the developer would be denied before learning
      anything about the user;
    - always on with group membership only: it reverses #361's decision for every project on upgrade.
- **D-16 — The page follows #366's rules.**
  - Stock Bootstrap 5 markup, classes through the class registry with new `manage:*` keys for the outcome badges
    (#366 D-15).
  - No inline JavaScript, handlers or styles (#366 D-30). The expandable traces are native `<details>`.
  - A "?" button to a new section of `docs/reference/manage.md` (#366 D-24).
  - Translatable wording.

#### Fit with #366

- **D-17 — What this design needs from #366.** All three are already in #366:
  - the requirement method on views (#366 D-27), for the own-requirement step and its label;
  - the matrix row's data method takes a user (#366 D-05);
  - the manage page's data methods take the ViewSet and the user and don't read the request (#366 D-13).
- **D-18 — Order of work.** #366 lands first. Within this issue: the recorder and trace function, then the
  command, then the page form.

#### Tests and docs

- **D-19 — The recorder is proven harmless by the existing suite.**
  - The whole existing test suite runs a second time with a recorder switched on for every request, and every test
    must pass unchanged. One extra run in CI, no new test code beyond the switch.
  - This is a real proof because many of those tests already assert the exact order of permission checks and the
    exact number of queries (`tests/test1/test_ancestor_authorization.py:100-118`,
    `tests/test1/test_ancestor_costs.py:97,132`, `tests/test1/test_ancestor_operations.py:77-88`). A recorder that
    added a query or reordered a check would fail them.
  - It requires the recorder to be switchable from outside a view, which the context variable gives (D-02).
  - Rejected: a new harness that replays requests with and without a recorder and compares responses byte by
    byte. Much new code, and form pages differ per request.
- **D-20 — The trace is proven faithful by a new grid suite.**
  - One parametrised test over two axes:
    - **kind of view:** plain, permission-required, Guardian object, Guardian list, nested Guardian create, manage,
      Resource, and two levels of nesting with cascade on and off;
    - **actor:** anonymous, inactive, no rights, model permission, object grant, superuser.
  - For each cell, one real GET and one trace of the same path and user must agree: 200 with allowed, 403 with
    denied, 404 with not found, a redirect to the login URL with login redirect.
  - The suite also has one case each for the outcomes outside the grid: error, no such route, a "not evaluated"
    step (D-22) and the login middleware (D-23).
  - Limit: the grid proves the trace for the view types the library ships. A project's own gate is one opaque step
    (D-08) and can't be proven upstream.
  - Rejected: a handful of hand-picked cases. The combinations nobody thought of are where a trace would be wrong.
- **D-21 — Docs.**
  - A new page or section for `cv_access`, with the JSON shape.
  - `docs/reference/settings.md`: the new setting, and "Diagnose the signed-in account" reworded: the trace is the
    first choice, signing in as the user the fallback.
  - `docs/reference/manage.md` (from #366): the Access check card.
  - `docs/reference/guardian.md` and `docs/reference/nested.md`: a pointer where they explain denials.
  - The `de` locales of the packages get the new strings.

### Remaining planning discretion

- The recorder's class and method names, and the name of its context variable (D-02).
- The trace object's field names, and the exact JSON shape behind its `version` key (D-13).
- How colours are applied to JSON without a new dependency (D-13).
- The module that holds the trace function.
- How the synthetic request is built (D-03), e.g. which request attributes project mixins may expect.
- The exact class-registry key names and the wording of labels (D-16).
- Whether the two forms in the card share one username field.

## Acceptance criteria

**Trace**
- A trace of a top-level core view reports the route, the own permission and the action state, and the right
  outcome for a user with and without the permission.
- A trace of a nested request lists the planned ancestor gates with their source labels, the gates that ran, and
  the remaining ones as "not reached" after a denial.
- A Guardian object view reports whether access came from an object grant or from the model-permission fallback.
- A Guardian list reports "sees n of m objects".
- A nested Guardian create reports the parent requirement and no own permission.
- The manage view reports the group gate and the mode (`CRUD_VIEWS_MANAGE_VIEWS_ENABLED`).
- An anonymous user gets "login redirect" where the endpoint redirects; an inactive user gets "denied".
- A missing ancestor or object gives "not found" with the lookup that missed.
- A nested endpoint without its `actions` entry gives "error" with the exception's class and the library's
  message.
- A project view that overrides `has_permission()` and returns `False` gives a "custom gate" step.
- A Resource object view is traced through its ancestors, its own permission, the item lookup and the action
  state. A missing item gives "not found". A Resource list reports its row count.

**Safety**
- No view handler runs during a trace (test with a handler that raises).
- A gate hook that writes to the database leaves no row behind after a trace.
- The whole existing test suite passes unchanged in a second run with a recorder switched on for every request
  (D-19).
- The grid suite passes: for every kind of view and actor in D-20, the trace's outcome matches the real GET.
- A view with a handler-phase check carries a "not evaluated" step with its reason (D-22): a workflow view, a
  nested list, a delete view and a form view.
- With `LoginRequiredMiddleware` installed, an anonymous trace of a plain view gives "login redirect"; without
  it, "allowed". Every trace carries the line about untraced middleware and URL decorators (D-23).

**Command**
- `cv_access <path> <user>` prints the text form; `--as-json` prints one valid JSON document with a `version` key.
- Output is coloured on a terminal, in both forms. `--no-color` removes every colour code, and so does piping the
  output.
- `--anonymous` traces the anonymous user. A username and a primary key both select a user.
- Exit codes: 0 allowed; 1 denied, not found or login redirect; 2 for an unknown user, a path without a route or
  an error.

**Page form**
- With `CRUD_VIEWS_MANAGE_ACCESS_TRACE` unset, the manage page has no Access check card, and its GET parameters
  change nothing.
- With it on, a manage-group member gets:
  - for a username: that user's matrix row and one outcome line per view, object views saying "needs an object
    pk";
  - for a username and object pk: an outcome for every view, each expandable to its trace;
  - for a username and a path: the full trace.
- On a nested manage page, the parent pks come from the page's URL.
- An unknown username shows a message and no result.
- The viewer needs no access to the traced path's parents.
- The card contains no inline `<script>`, no `on*` attribute and no `style` attribute, and its classes resolve
  through the class registry.

**Docs**
- The docs named in D-21 exist, and the settings reference lists `CRUD_VIEWS_MANAGE_ACCESS_TRACE` with its
  default.
