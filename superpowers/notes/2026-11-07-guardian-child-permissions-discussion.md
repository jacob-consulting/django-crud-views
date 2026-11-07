# Finding 23: Guardian parents and address permissions

Date: 2026-11-07. Status: open discussion; no upstream design or implementation chosen.

The user requested a code walkthrough of finding 23 and the tabler-test workaround. Keep this note updated as
the discussion changes. Do not stage or commit it unless subsequently requested. Findings 24 and 25 are outside
this discussion. The navigation-tabs part of finding 23 is not explored in this initial permission walkthrough.

## The concrete need

In tabler-test, Sam is an account manager with object-level `view_customer` and `change_customer` grants on selected
customers. Addresses belong to customers. The demo lets Sam manage addresses under those customers without
maintaining Guardian grants on every address row.

The actual grant helper in [sales/permissions.py](../../../tabler-test/example/sales/permissions.py) is:

```python
def grant_customer(user, customer, actions=("view", "change")):
    """Give ``user`` object-level permissions on ``customer`` (view and change unless told otherwise)."""
    for action in actions:
        assign_perm(f"sales.{action}_customer", user, customer)
```

Those grants do not themselves grant `view_address` or `change_address` on any address.

## What the package does today

The shipped Guardian update view explicitly combines a parent check and a child-object check:

```python
class GuardianUpdateViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, UpdateViewPermissionRequired
):
    pass
```

Source: [Guardian views](../../src/crud_views_guardian/lib/views.py).

For a nested Guardian address update using the defaults, an ordinary active user needs the configured parent
permission (`view_customer` by default) on the URL's customer and `change_address` on the address. Guardian list
views likewise check the parent and filter the child queryset by child grants. Per-view global-permission
fallback can change which grants satisfy those checks, but the parent and child remain separate checks.

Nested Guardian create is an existing exception: it checks the configured parent permission without requiring a
child-object grant or a model-level child-add permission. No child object exists yet.

Trying to compose only `GuardianParentPermissionMixin` with a core update view is explicitly rejected. This is
an excerpt of `_guardian_child_composition_error()` in [Guardian mixins](../../src/crud_views_guardian/lib/mixins.py):

```python
if cls.cv_object:
    if not issubclass(cls, GuardianObjectPermissionMixin):
        return "Object child views using GuardianParentPermissionMixin require GuardianObjectPermissionMixin."
```

There is an equivalent companion-mixin requirement for lists. These checks preserve the package's current
parent-plus-child authorization policy; removing the check alone would not establish a complete alternative.

A plain child `ViewSet` has a different limitation: naming a Guardian parent establishes nesting and queryset
scoping, but does not automatically run that parent's permission checks.

## What tabler-test actually uses

### Where to find the address list in the app

Open **Sales → Customers**, open a customer's detail page, then select **Addresses** in the page's action toolbar,
alongside Orders and Subscriptions. `CustomerDetailView` includes `addresses` in both `cv_context_actions` and
`cv_context_actions_inline`. It is a child-list link, not a separate sidebar entry or an embedded tab.
Sign in as `sam` to inspect this for customers granted to the account manager, or `alex` for the Owner's access.

### View composition

The customer is a `GuardianViewSet`. Addresses use a plain `ViewSet`. The following excerpts from
[addresses.py](../../../tabler-test/example/sales/views/addresses.py) omit the ViewSet's icon and the views'
presentation attributes for clarity:

```python
cv_address = ViewSet(
    model=Address,
    name="address",
    parent=ParentViewSet(name="customer"),
)

class AddressListView(CustomerGrantMixin, BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_address
    table_class = AddressTable
    # Presentation attributes omitted.

class AddressUpdateView(CustomerGrantMixin, BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_address
    form_class = AddressForm
    # Presentation attributes omitted.
```

The actual custom mixin is:

```python
class CustomerGrantMixin:
    """Deny the view unless the user holds the needed permission on the customer in the URL."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            action = "view" if getattr(self, "cv_permission", "view") == "view" else "change"
            if not can_on_customer(request.user, action, self.cv_get_parent_object()):
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
```

It resolves the customer from the URL. An address operation with `cv_permission == "view"` requires customer
view permission. Every other operation requires customer change permission, including address creation,
deletion, and the custom make-default action. This is an application-specific mapping, not a general mapping
from HTTP GET/POST to read/write: opening an update form already requires change permission.

The helper in [permissions.py](../../../tabler-test/example/sales/permissions.py) accepts either a model-wide
customer permission or a Guardian grant on the particular customer:

```python
def can_on_customer(user, action, customer) -> bool:
    """Model-level permission (Owner, Roasters) or an object grant (account managers)."""
    return user.has_perm(f"sales.{action}_customer") or ObjectPermissionChecker(user).has_perm(
        f"{action}_customer", customer
    )
```

Calling `super().dispatch()` preserves the ordinary address model-permission check in the core
`*PermissionRequired` view. Anonymous requests continue into that ordinary permission/login handling.

The [seed setup](../../../tabler-test/example/sales/seed.py) gives the Account managers group all four address
model permissions. This is a shortened excerpt of the actual call; other model permissions are omitted:

```python
Group.objects.get(name="Account managers").permissions.add(
    *(perm(f"{a}_address") for a in ("view", "add", "change", "delete")),
)
```

Here `perm()` retrieves the corresponding `sales` Permission row. No per-address Guardian grants are needed
for these views. The group's address permissions and the customer's grants serve different purposes.

## Effective rules and parent scoping

For an ordinary active authenticated user, the permission requirements are:

| Address operation | Permission on the URL customer (object grant or model-wide) | Address model permission |
| --- | --- | --- |
| List/detail | `view_customer` | `view_address` |
| Create | `change_customer` | `add_address` |
| Update/make default | `change_customer` | `change_address` |
| Delete | `change_customer` | `delete_address` |

This table describes permission requirements; object existence, nested scoping, action state, and form
validation still apply. Notably, deleting an address requires customer **change**, not customer delete.

The core [ViewSet.get_queryset](../../src/crud_views/lib/viewset/__init__.py) separately filters children by the
URL parent. For this single-FK relationship, its effect can be illustrated as follows (explanatory pseudocode,
not an additional implementation in tabler-test):

```python
Address.objects.filter(customer__pk=view.kwargs["customer_pk"])
```

Thus naming an allowed customer in the URL cannot expose an address belonging to another customer. The
ordinary object lookup searches the scoped queryset and returns 404 for that mismatch. The parent permission
check answers whether the user may act under this customer; the queryset ensures the requested address really
belongs there. `CreateViewParentMixin` supplies the URL parent for address creation.

## What this demonstrates, and what remains open

The workaround is **customer permission plus address model permission**, without per-address grants. It is
not strictly parent-only authorization. Sam's group supplies broad address capabilities, while customer grants
restrict where those capabilities may be used. Removing a group-level address permission still denies the
corresponding operation even if Sam retains the customer grant.

The mixin adds request enforcement only. It does not override the core action/link access helpers; we should
not assume all rendered buttons reflect the added customer check. No navigation solution is proposed here.

Existing [tabler-test customer tests](../../../tabler-test/example/sales/tests/test_customers.py) contain
assertions for allowed customer address access, denied access under other customers, address updates, and
cross-parent 404 responses. These tests were read, not executed for this discussion. The explanation is based
on source inspection; no implementation changes or runtime verification were performed.

## Maintainer's interpretation and concern

The maintainer identifies the relevant composition as a Guardian parent ViewSet with a default/core child
ViewSet. The user has Guardian object grants on selected parents and ordinary model permissions on the child.
They dislike the downstream `CustomerGrantMixin` intercepting requests and expect nested ViewSets to check
every object traversed by the URL. This is an open discussion, not approval of an implementation.

Their description of the risk matches the current code: without the custom parent gate, a user with address
model permissions can name another customer and an address belonging to that customer in the nested URL.
The queryset's relationship filter succeeds because the two objects match, and the child model permission
also succeeds. Neither check asks whether the user has access to that customer.

Two cases must remain distinct:

| URL contents | Existing parent-scoped child queryset | Custom customer permission gate |
| --- | --- | --- |
| Allowed customer with another customer's address | No matching address; object lookup returns 404 | Customer check can pass, but does not defeat queryset scoping |
| Forbidden customer with that customer's own address | Matching address; relationship is valid | Denies the customer operation with 403 |

This is the difference between relationship validation, which core nesting already performs across the
configured parent chain, and ancestor authorization, which core child views do not automatically perform.
The Guardian parent ViewSet's view dispatch is not invoked merely because its object appears in a child URL.
The child's view handles the request. The custom mixin supplies the missing parent authorization in this demo.

The maintainer's expectation may motivate an upstream nesting contract, but the exact permission to check
on an ancestor is still undecided. A parent object in a URL does not itself choose a parent view/action:
opening an address editor could require customer view permission, customer change permission (the demo's
policy), or another explicitly configured permission. Existing Guardian child defaults generally check parent
view permission even for child updates, while the demo checks parent change permission for address writes.

Current discussion question: should editing an address require permission to view its customer, or permission
to change that customer as the demo currently requires?

### Scenario-specific answer

The maintainer prefers **change permission on the customer** when editing an address. Addresses belong to the
customer and form part of its configuration: managing the customer should allow managing its addresses.
The maintainer explicitly notes that other real-world relationships can require different rules. This is a
decision for this scenario, not approval of a universal ancestor-permission mapping or a particular API.

One distinction still needs clarification: should customer change permission be sufficient for address
management, or should the existing child permission remain an additional requirement? The current demo
requires both customer change permission and the applicable address model permission. Selecting the parent
permission alone does not settle whether to retain that independent child gate.

The maintainer asked to retain that question while examining an existing entity-role group pattern in a
separate project. The sanitized [entity-role pattern analysis](2026-11-07-entity-role-permission-pattern-analysis.md)
records the delegated read-only review. It finds object-granted Guardian children on the representative routes,
with immediate-parent checks, and separates that protection from the still-unresolved all-ancestor guarantee.
The review itself chose no parent permission policy; the subsequent scenario-specific answer above selects
customer change permission for address editing, with child-gate semantics still open.

## Technical possibility: a child with no independent permission gate

The maintainer asked whether a complete parent authorization gate would remove the technical need to assign
address permissions. Yes: plain core views (for example, UpdateView instead of UpdateViewPermissionRequired)
can omit the independent child permission check, provided every endpoint is covered by the appropriate parent
gate and nested relationship validation. A separate route requires its own authorization. A ViewSet does not
itself enforce a model permission; the concrete view classes and their permission mixins enforce it.

This was a technical clarification, not agreement to adopt parent-only authorization or a recommendation to
remove child permissions.

## Three levels with an intermediate level without a permission gate

The maintainer then asked about a permission-protected child below an address level that has no independent
permission gate. Use **customer → address → delivery instruction** as a hypothetical example. Delivery
instructions are illustrative, not a proposed feature.

For a proposed all-ancestor policy where changing delivery instructions is treated as managing customer
configuration, the conceptual checks would be:

| Level | Relationship/existence validation | Permission requirement for instruction editing |
| --- | --- | --- |
| Customer | Resolve the URL customer | Customer change permission under this scenario's policy |
| Address | Resolve the URL address under that customer | No independent address permission, if explicitly configured that way |
| Delivery instruction | Resolve the instruction under that address | Its own change permission, enforced by its view's configured permission system |

All applicable permission gates must pass. The absence of an address permission gate does not terminate
ancestor traversal, erase the customer's gate, or waive the instruction's own permission requirement. A user
with instruction change permission but without customer change permission is denied under this hypothetical
policy. A matching customer/address/instruction relationship remains required even at levels without a gate.

This is a conceptual answer, not current package behavior or an agreed implementation. The current core does
not provide that recursive ancestor authorization, and the current Guardian parent mixin checks only the
immediate parent. Configuring its immediate-parent permission as None does not make it discover/check a higher
ancestor.

An unresolved design requirement is how to declare ancestor policy independently of incidental view classes:
the address's own view being unprotected does not by itself say which ancestor checks should apply when a
deeper view is requested. An explicit absence of a gate must also remain distinguishable from an invalid or
missing permission declaration, which must not silently grant access. No API has been selected.

The higher ancestor's required action is also policy, not something inferable solely from URL structure or a
matching permission name. The illustrative customer-change requirement above extends the configuration
interpretation to delivery instructions; the maintainer has not yet selected that deeper relationship's policy.

## Agreed traversal behavior and possible shared contract

The maintainer confirmed the conceptual behavior: every level contributes its configured restriction; a level
without its own permission gate contributes no additional permission requirement and does not stop traversal.
They asked whether this implies something like an AuthTraversalMixin contract shared even by plain views and
ViewSets.

Conceptually, every nested endpoint must participate in the same ancestor-authorization mechanism, including
plain views. Otherwise requesting a plain endpoint could bypass the ancestor restrictions that protect a
permission-required sibling. This does not necessarily require adding a mixin explicitly to every concrete
view, or making both View and ViewSet inherit the same mixin. A shared base hook or delegated checker could
provide the same behavior; no implementation approach has been selected.

Two responsibilities remain distinct:

- Traversal resolves/validates the configured URL ancestry and evaluates applicable ancestor policies without
  stopping at a level with no independent gate.
- Local authorization enforces the endpoint's own permission model: none, model permissions, Guardian object
  permissions, or an explicitly supported custom policy. Existing endpoint-specific behavior such as Guardian
  queryset filtering must not be assumed equivalent to a simple boolean object check.

The ViewSet/nesting configuration could describe ancestry and ancestor policies, while a common view entry
point invokes enforcement. This is an explanatory possibility, not an approved API or implementation plan.
Ancestor checks should evaluate declared policy on resolved objects, not execute ancestor views or simulate
requests to them. An explicitly absent local gate is different from an invalid or missing policy declaration.

Compatibility and adoption remain open: sharing a contract does not decide whether stronger ancestor checks
are automatic for existing applications or enabled explicitly. Maintainability remains a hard constraint.

## Candidate enablement controls and request cost

The maintainer is undecided about automatic enforcement because it adds request work and project requirements
vary. They proposed enforcement by default, with a global disable setting and possibly ViewSet/view overrides.
This remains a candidate, not a settled default or API.

A possible precedence is explicit view setting, then explicit ViewSet setting, then the global setting. Local
settings need an inherit state distinct from enabled and disabled. If these are ordinary fallback settings,
global disabled is a default and an explicit local enabled can override it; a global hard kill switch would
have different semantics and should not be implied by the same description.

Two controls have different meanings and must not be conflated:

- An ancestor contributes no local permission requirement: continue checking higher ancestors and relationships.
- The requested endpoint disables ancestor traversal: no ancestor authorization is supplied by this mechanism.
  Its existing local checks and relationship scoping still apply. In a plain child view this can restore the
  original exposure if no other parent authorization exists.

If endpoint overrides are supported, the resolved setting belongs to the requested endpoint. An ancestor's
own endpoint-disable setting must not silently terminate a descendant's enabled traversal. Ancestor policy
and endpoint enablement are separate concepts.

Potential cost includes ancestor resolution and permission evaluation, depending on depth and backend; no
query counts or timings have been measured. A bounded implementation should reuse request-local resolved
objects and permission work where practical, avoid duplicate existing Guardian checks, and avoid persistent
cross-request permission caches. Stronger authorization still has an unavoidable cost when required objects
or grants have not otherwise been checked. Exact integration remains unplanned.

Default-on enforcement would change behavior for existing nested applications and may deny previously
accepted requests. A global disable switch would help migration but does not make that default backward
compatible. A possible bounded starting scope is global control plus a ViewSet override, adding view-level
exceptions only for a concrete endpoint need; no scope has been chosen.

Next clarification: does the maintainer have a concrete case requiring one view within a ViewSet to bypass
ancestor enforcement while sibling views retain it, or is project/ViewSet-level control sufficient initially?

## Clarification: which ancestor permission is required?

The maintainer returned to the choice between change and view permission. Only customer change permission
for address management has been selected so far; neither a universal change default nor a universal view
default has been agreed.

The assistant proposes this default for standard CRUD operations, subject to maintainer agreement:

| Requested child operation | Proposed ancestor permission |
| --- | --- |
| List/detail | view |
| Create/update/delete | change |

The rationale is that reading child configuration reads its container, while changing that configuration
changes the container without creating or deleting the container itself. Under this proposal, deleting an
address requires customer change permission, not customer delete permission. Local child permissions remain
whatever the child endpoint independently requires.

This is an operation-based mapping, not an HTTP-method mapping: opening an update form already requires the
change ancestor permission. Non-CRUD/custom actions require an explicit policy rather than guessing from GET,
POST, or an unfamiliar permission key. Relationships with different semantics need an override. This proposal
has not settled the representation, configuration location, or policy for every higher ancestor.

### Confirmed default mapping

The maintainer confirmed that views in the same child ViewSet can require different permissions on their
parent, accepting the standard CRUD mapping above: list/detail require parent view; create/update/delete
require parent change. Different relationship requirements remain configurable. Child-local permission checks
remain separate when present. No configuration names or implementation approach have been approved.

The earlier proposal wording is retained as discussion history and superseded by this confirmation for the
standard CRUD parent mapping. Its application to every higher ancestor in deeper nesting still needs an
explicit decision; the existing agreement to traverse all ancestors does not itself select each one's action.

## Proposed deeper-chain default: nearest protected ancestor change, higher ancestors view

The maintainer proposes this default for writes: require **change** on the first ancestor with an active
permission gate, then **view** on higher ancestors with active permission gates. Intermediate levels without
permission gates do not consume the change requirement. All relationship/existence checks continue through
the entire configured ancestry. Projects may instead require change throughout the protected ancestry.

Here "parent" in the permission rule means the nearest protected ancestor, which may differ from the immediate
structural parent. For customer → address (no independent permission gate) → delivery instruction, an instruction
write requires customer change permission. If the customer itself is below a protected organization, that
organization requires view permission under this proposed default. The instruction's own local permission
requirement remains independent.

| Ancestor relative to the requested endpoint | Read operation | Write operation under proposed default |
| --- | --- | --- |
| No active local permission gate | No local permission check; continue traversal | No local permission check; continue without consuming the change requirement |
| Nearest ancestor with an active permission gate | view | change |
| Higher ancestor with an active permission gate | view | view |

The assistant recommends this as a reasonable default: the nearest protected container controls changes to
its contents, while higher containers control access to their scope. Requiring change on every ancestor can
be a stricter project policy but may deny delegated management of an inner container to users intentionally
allowed only to view its outer container. Neither policy fits every domain, so the difference must remain
explicit and configurable.

"Has a permission gate" must be determined by declared policy, not by whether the user happens to have a
grant or whether permission rows exist. A failed/misconfigured gate must deny/report an error, never be
treated as an unprotected level and skipped. Endpoint traversal enablement remains separate from whether an
ancestor contributes a local gate. Exact representation of that policy is unresolved.

If the entire ancestor chain is explicitly unprotected, there is no ancestor grant to require; local endpoint
authorization and relationship validation still apply. This is distinct from a missing or invalid declaration.

This is the maintainer's proposed default and the assistant's recommendation, pending confirmation. A possible
bounded configuration offers this policy and change-on-all-protected-ancestors for writes, preserving explicit
overrides for other relationship semantics. No option names, implementation, or broader configuration scope
have been selected.

### Confirmed deeper-chain default

The maintainer confirmed the proposed default: writes require change on the nearest protected ancestor and
view on higher protected ancestors; reads require view on each protected ancestor. Explicitly unprotected
levels do not stop traversal or consume the nearest-ancestor change requirement. Relationship validation
continues throughout, and the endpoint's own permission checks remain independent. Stricter requirements
must be configurable. This confirmation supersedes the pending-confirmation wording above.

Outstanding configuration choices include default enablement, the scope of opt-outs (global, ViewSet, view),
the scope/representation of stricter ancestor policies, and explicit handling of custom actions. No design
document or implementation has been approved, and no files have been staged or committed during this discussion.

## Confirmed first-wave configuration scope

The maintainer selected **global and ViewSet-level controls only** to keep the scope bounded. Per-view traversal
overrides are deferred to a possible second wave; they are not part of the initial design or implementation.
This supersedes earlier candidate precedence involving an explicit view setting.

The first-wave configuration precedence is therefore an explicit ViewSet value over the global default.
The agreed operation-dependent permission mapping still applies: different views within one child ViewSet
can require different ancestor permissions because list/detail are reads and create/update/delete are writes.
That behavior does not require per-view traversal configuration.

Global/ViewSet enablement defaults, exact option names, and custom-action classification remain unresolved.
The maintainer previously proposed enabled by default but had not yet confirmed that choice. No implementation
or design document approval follows from this scope decision.

## Confirmed default-on enforcement

The maintainer confirmed **ancestor enforcement enabled by default**, with global and ViewSet-level opt-outs.
Their reason is to protect developers new to the package from accidentally omitting ancestor authorization
when composing nested views. This supersedes the earlier uncertainty about the enablement default.

This default addresses the identified ancestor-check omission; it is not a guarantee against all authorization
mistakes. Explicit opt-outs, incorrect policies, custom overrides, and unsupported compositions still require
clear validation and documentation. Existing endpoint-local permission enforcement remains independent.

The behavior change for existing nested applications is intentional under this decision. The design must
explain the migration and opt-out behavior, and avoid silently treating unknown policy declarations as no
permission requirement. No implementation is authorized yet.

The next unresolved behavior is custom-action classification: standard CRUD operations have an agreed
read/write mapping, but a nonstandard action must not silently receive a weaker policy merely because its
permission key is unfamiliar. A possible bounded rule requires a ViewSet-level declaration for actions whose
required ancestor policy cannot be established from the supported standard operations. This is a proposal,
not a confirmed requirement or API.

## Confirmed custom-action requirement

The maintainer confirmed that an unrecognized custom action requires an explicit ancestor-policy declaration
on its ViewSet. A missing declaration is a configuration error; it must not silently become read access or
an unrestricted action. This supersedes the proposal status above. The declaration's exact syntax and the
definition of recognized standard operations remain design details to resolve, preserving the distinction
between an operation and its HTTP method.

## Implementation approaches for discussion

The behavior is sufficiently grounded to compare two ways of obtaining an ancestor's permission policy.
Neither approach is selected yet; this is not an implementation plan.

1. **Explicit ViewSet policy, evaluated by a shared traversal.** Each ancestor exposes a declared policy for
   model permissions, Guardian object permissions, or explicitly no independent permission gate. The shared
   request entry point resolves the chain and asks each policy to authorize the required operation. Existing
   endpoint-local checks and Guardian queryset filtering remain in their established paths. This is explicit
   and works even when the ancestor has no corresponding detail/update endpoint. Its cost is policy
   configuration alongside the existing view-class choices, and the design must make contradictions visible
   rather than silently applying weaker defaults. Exact defaults and declaration syntax remain unresolved.
2. **Infer ancestor policy from registered permission-aware views.** Resolve the ancestor's relevant view and
   reuse its access helper where possible. This reduces duplicate configuration in conventional ViewSets, but
   requires rules for missing detail/update views, differently protected sibling views, custom overrides, and
   view helpers whose semantics do not match ancestor authorization. No ancestor dispatch should be invoked.
   Explicit fallback/error rules would still be necessary; the current helpers do not establish a complete
   traversal contract by themselves.

The assistant recommends the explicit ViewSet policy because the maintainer requires a distinction between
an intentionally unprotected level and a missing/misconfigured gate. It also keeps ancestry policy independent
of which UI endpoints happen to be registered. This recommendation must be assessed against the added
configuration burden and the project's maintainability rule. The maintainer has not chosen an approach.

### Selected approach

The maintainer selected **explicit ViewSet policies**, superseding the undecided status above. Ancestor policy
must not be inferred from registered detail/update views. Concrete syntax, defaults, and compatibility details
still require a reviewable design. The design draft stays in the notes directory without staging or committing
and receives a builder review before handoff.

The written design's builder review is complete. The remaining maintainer questions are legacy Guardian
settings migration, provider defaults, and whether broad button/link permission parity can remain outside
the first wave. The author's recommendation is explicit migration errors instead of a translation layer,
model/strict-Guardian provider defaults with explicit none, and request enforcement first. Global-default
precedence and the initial supported ORM relationship boundary are marked author choices for review.

### Legacy migration clarification

The maintainer asked whether rejecting old Guardian settings is complex and clarified that they manage all
downstream projects. A simple constructor/configuration check for removed public keys is bounded; the package
already uses a before-validator to reject a removed Guardian ViewSet option. Arbitrary subclass overrides need
an explicit supported declaration rule rather than elaborate introspection.

The larger cost is the draft's proposal to preserve the legacy parent policy when traversal is disabled,
which requires keeping two parent-authorization behaviors and maintaining their helper semantics. Given the
controlled downstream migration, the assistant proposes a direct breaking migration instead: replace the
legacy ancestor permission mechanism, reject old public settings with a migration message, and migrate the
managed applications explicitly. Do not build automatic translations or a lasting legacy execution mode.

This changes the draft's proposed opt-out semantics: disabling traversal would disable ancestor permission
enforcement from this mechanism, including the old Guardian parent-permission gate. Existing child object/model
permissions and relationship scoping remain; independent state/authentication behavior must be preserved as
required. This consequence needs maintainer confirmation before replacing the earlier compatibility proposal.

### Impact of removing the old Guardian ancestor permission gate

The maintainer requested an explanation before deciding. When new traversal is enabled, its checks replace
the old gate; ancestor protection is not simply removed. The default policy can be stricter: writes require
change on the nearest protected ancestor rather than the old default parent view, and higher ancestors are
also checked. Equivalent existing custom requirements need explicit migration to the new declarations.

When new traversal is disabled and no legacy fallback remains, the old immediate-parent permission denial
also disappears. Guardian object views still require the child's object permission, and lists still filter
children by grants, but these do not imply permission on the parent. A user retaining child grants after losing
the parent grant can reach those children under this opt-out. A plain child with only model permissions can
again exhibit the original demo gap. None of this automatically changes existing grants or group memberships.

Important correction to broad statements that child checks remain: existing nested Guardian create deliberately
has no child-object check and no model-level child-add check. Its permission gate is the parent check. Merely
removing that gate while preserving the rest of the old composition can leave an authenticated active user
able to create under a parent without any permission authorizing that creation. An action-state hook is not
a replacement authorization policy, and selecting a real parent does not prove permission to use it.

The disabled-mode contract for nested Guardian creation therefore remains an explicit unresolved decision:
should it require child model add permission, require a declared application gate, or allow intentional absence
of a permission gate under the explicit opt-out? Do not silently pick a behavior or call all local checks
unchanged without stating that this particular child gate does not exist today.

Removing the ancestor permission check does not authorize removal of the mixin's separate authentication,
inactive-user, or create action-state responsibilities. Relationship validation also remains distinct: existing
queryset scoping protects object lookups but is not equivalent to the new full-chain create validation.

### Proposed narrower performance switch

The maintainer clarified that performance concerns motivated disabling the parent-check cascade. The assistant
therefore proposed replacing the earlier all-or-nothing opt-out with two modes of the same mechanism:

- Cascade enabled (default): nearest protected ancestor requires change for writes/view for reads, followed
  by the configured checks on higher protected ancestors.
- Cascade disabled: skip explicitly unprotected ancestors until reaching the nearest protected ancestor,
  enforce its required permission, then perform no higher ancestor permission checks.

A denial at that nearest gate still denies the request; it does not cause the algorithm to try another gate.
If there is no protected ancestor, there is no ancestor permission requirement to evaluate. Endpoint-local
permissions remain independent in either mode.

The stopping point concerns permission evaluation, not URL relationship validation. The complete declared
relationship chain must remain valid in both modes. This can still require loading or querying higher
ancestors, so the optimization is bounded and unmeasured rather than a promise of eliminating all ancestor work.

This proposal avoids preserving an old Guardian execution mode or inventing a disabled-mode child-add fallback
solely because of the performance switch: the nearest ancestor gate remains. Explicitly all-none ancestry
still needs its documented intentional-unprotected semantics. The maintainer asked to confirm this meaning;
the narrower switch is not yet accepted. Earlier opt-out decisions should be reconsidered if it is selected.

### Confirmed cascade-depth switch

The maintainer accepted the narrower switch because it is easy to explain. The global/ViewSet switch controls
permission-check depth: default on checks the entire protected ancestry; off still checks the nearest protected
ancestor, passing through explicitly unprotected levels, then omits higher permission checks. Relationship
validation continues across the whole URL chain in both modes. Endpoint-local permissions stay independent.

This supersedes the previous total-opt-out interpretation and removes the need for either a legacy Guardian
parent-check fallback or a new child-add fallback solely because cascade is disabled. The design draft has
been rewritten to present the agreed current semantics rather than leave contradictory alternatives in its
operative sections. Provider defaults and navigation scope remain under discussion. Nothing is staged or
committed, and the design is not yet approved for implementation.

### Reaffirmed hard constraint: readable and maintainable implementation

The maintainer explicitly reaffirmed that human readability and maintainability must be ensured, invoking the
Zen of Python. Complex code that happens to work is not an acceptable outcome. The design now has concrete
acceptance criteria for an explainable request flow, bounded explicit helpers, a clear enforcement entry point,
limited measured reuse, actionable configuration errors, and no speculative policy framework. If the scope
requires excessive complexity, simplify or narrow it rather than treating passing tests as sufficient.

This instruction does not answer the pending provider-default question: model permissions for core ViewSets,
strict object permissions for Guardian ViewSets, and explicit none for unprotected ancestors remain proposed.

### Confirmed ancestor provider defaults

The maintainer confirmed model permissions for core ViewSet, strict object permissions for GuardianViewSet,
and explicit none for intentionally unprotected ancestors. Defaults come from the ViewSet type without
inspecting registered views. They govern the ViewSet's contribution as an ancestor and do not change its own
endpoint-local permission checks. This supersedes the pending-default wording above.

The earlier proposed optional Guardian global-permission fallback was not included in this confirmation.
Navigation/button integration remains open: request enforcement is required, while broad visibility parity
would expand the first-wave scope and needs a separate decision.

### Confirmed request-only first wave

The maintainer accepted that existing buttons/links may lead to destinations denied by the new ancestor checks.
First-wave scope is request enforcement; full visibility consistency is deferred to separate work. Existing
helpers affected by removed configuration still need bounded migration to remain valid, but this does not
authorize broad traversal integration across navigation/rendering helpers.

### Confirmed optional Guardian model-permission fallback

The maintainer confirmed an explicit ViewSet ancestor-policy option accepting global model permission as an
alternative to the required object grant. It is disabled by default. It allows globally privileged roles and
object-scoped roles to satisfy the same ancestor requirement without changing the endpoint's own Guardian
policy. The design draft now incorporates this decision.

The design is ready for maintainer review. Author choices presented with it are explicit ViewSet-over-global
cascade precedence, direct migration with clear removed-setting errors, and the initial supported ORM ancestry
boundary. No design approval, implementation, staging, or commit has occurred.

### P-01 approved; decision tables requested

The maintainer approved explicit requested-ViewSet cascade values overriding the global default in either
direction; unset inherits. The global setting is a default, not a master switch, and an ancestor's own cascade
setting does not interrupt a descendant request. P-01 is now a settled decision in the GSD ledger (D-26).

The maintainer requested retaining the precedence table and adding other useful decision tables. The design
now includes tables for cascade responsibilities, provider defaults, Guardian global fallback, standard
operations, a four-level worked example under both modes, and independent ancestor/endpoint gate outcomes.
These tables explain already agreed behavior and do not approve P-02 or P-03. P-02 is the next discussion item.

### P-02 approved after code walkthrough

The maintainer approved the direct migration proposal after inspecting actual Guardian settings, their use
on the test application's child Book ViewSet, and `_guardian_resolve_parent_perm_key()`. The code walkthrough,
old permission/fallback tables, and approved migration table are retained in the design.

Explicit `cv_guardian_parent_permission` or `cv_guardian_parent_create_permission` declarations must produce
an actionable configuration error after removal, including None/former defaults and application subclass
field declarations. Implicit former library defaults do not count as explicit declarations. No automatic
translation, ignored legacy policy, or old execution mode is retained. Independent authentication, inactivity,
state, and child object/queryset checks remain; endpoint-local `cv_guardian_accept_global_perms` is not removed.
P-02 is recorded as D-28. P-03 remains open; implementation and final design approval are still pending.

### P-03 approved; behavioral closure remains

The maintainer approved ORM-only nested ancestry using supported declared FK/M2M relationships. Unsupported
metadata and any Resource in a nested chain (ancestor or endpoint) produce configuration errors in either
cascade mode. Top-level Resources retain existing behavior. P-03 is recorded as D-29, superseding the draft's
earlier option to leave Resource endpoints beneath ORM ancestry to an implementer's assessment.

P-01–P-03 are now settled. The maintainer's instruction to leave no behavioral decisions open still requires
auditing anonymous responses, operation classification, failure ordering, the public configuration contract,
and bounded migration of existing helper consumers. These items are listed explicitly in the GSD handoff;
they do not authorize implementation or reopen the approved requirements.

### B-01 approved: anonymous and denied responses

The maintainer approved preserving the requested endpoint's existing supported anonymous/no-permission policy,
defaulting to login redirect when protected ancestry is encountered. Existing anonymous 403/404 settings are
preserved. Authenticated permission denial and inactive users encountering protected ancestry receive 403.
All-none ancestry introduces no additional login requirement; existing endpoint/Guardian actor rules remain.
No new per-view traversal setting is introduced. B-01 is recorded as D-30; error ordering is separately B-03.

The next question, B-02, makes the finite built-in operation classification and explicit custom-action
declaration semantics concrete. Its proposed table is in the design, pending maintainer confirmation.

### B-02 approved; operation table retained

The maintainer approved the finite operation table and requested retaining it. List/card/detail families are
reads; create/update/delete families, polymorphic create selection, and built-in ordering actions are writes.
Manage is a read for ancestry with its administrative gate retained. Generic actions, custom forms, workflow,
and other unknown endpoints require explicit ViewSet declarations. Fragments use the editor's requirements.
Normal subclasses retain family semantics; names/HTTP methods/local permission keys alone cannot classify
generic custom behavior. An explicit ViewSet action entry overrides the standard ancestor requirements.
B-02 is D-31. The table is marked approved; exact public syntax remains B-04.

The next behavioral question is B-03: validate static configuration, apply actor policy, then resolve ancestors
outermost inward and stop at the first reached structural/permission failure before endpoint processing.
The proposed ordering and example-result tables are in the design pending approval.

### B-03 approved; interleaved top-down checks

After confirming that each ancestor's relationship/existence and selected permission are checked together
before continuing deeper, the maintainer approved B-03 and requested its table in the specification. The
ordering table, failure-example table, and a top-down Organization/Customer/Address walkthrough are retained
and marked approved. Nearest-protected selection happens from configuration before ORM lookups; cascade-off
still validates higher relationships but does not evaluate higher permissions. The first reached failure
stops processing. B-03 is recorded as D-32; public configuration B-04 and bounded helper migration B-05 remain.

### B-04 approved: configuration-only policy class

The maintainer questioned avoiding a policy class, then clarified that it should perform no permission checks
and approved B-04. The selected approach is a small typed configuration/validation object, consistent with
existing Pydantic patterns. Shared traversal owns relationship resolution, permission evaluation, and request
denial. No execution framework, plugin registry, or policy-subclass discovery is introduced.

The representation comparison table and responsibility table are retained in the design. The earlier flat
ViewSet-field proposal is superseded and removed from the operative API section. D-33 records the decision.
A complete public schema still needs to be written down before final design approval; unshown names or
validation combinations must not be attributed to this approval. B-05 remains open.

### B-05 approved; helper migration table retained

The maintainer approved the bounded helper migration and requested its table in the design. Existing helpers
use the new provider/fallback and target operation requirement for the immediate parent they already check.
An immediate none policy skips that local permission check while retaining actor/state/custom denials; helpers
do not gain higher-ancestor traversal. Missing required parent context retains existing unavailable/False
behavior, and invalid configuration is surfaced rather than hidden or treated as permission success.

Manage diagnostics display replacement policy/cascade/requirements/fallback distinctly from endpoint-local
Guardian settings. Its administrative access gate is unchanged. Full navigation parity remains deferred;
the request is authoritative. B-05 is D-34 and its table is marked approved.

All P-01–P-03 and B-01–B-05 decisions are approved. The concrete policy-class API still needs to be written
down and reviewed for consistency; the design as a whole and implementation have not been approved. Nothing
has been staged or committed.

### C-01 API shape approved

The maintainer approved the presented configuration API: `ViewSet.ancestor_policy`, `AncestorPolicy` with
provider/fallback/cascade/read/write/actions, and `AncestorPermissions(nearest=..., higher=...)`. The defaults,
explicit string none versus Python None inheritance, and complete-pair replacement are recorded in D-35.
Examples and the field table are retained in the design. Detailed validation is the next separate discussion
(C-02); exact global setting declarations also remain proposed. No implementation or Git changes authorized.

### C-02 validation approved; table retained in the spec

The maintainer approved the proposed validation rules, including requiring GuardianViewSet for the guardian
provider, and explicitly requested the table in the spec. C-02 and its table are marked approved as D-36.
Invalid/ineffective configuration is rejected; action registration is checked after registration completes.
Structural errors use Pydantic validation; registry/relationship errors have Django system checks and runtime
guards; selected missing permission keys fail at runtime without startup permission-table queries. Exact
global setting declarations remain open. No implementation, staging, or commits were performed.

### Remaining API declarations approved; status reconciled

The maintainer approved the proposed global cascade/read/write setting names and the public exports from
`crud_views.lib.viewset`. C-03/D-37 records the declarations and their scope in a decision table. All identified
product/API decisions are settled; final whole-design approval remains separate. Stale operative passages
about unnamed APIs, unfinished schema, and no commits were corrected. The earlier explicit commit request
produced `db4c2cc6` for the C-01/C-02 documentation update; this status update has not been committed.

### Final spec approved; planning explicitly deferred

The maintainer gave final approval of the complete spec and instructed: "do not write plan yet."
D-38 records that approval and constraint. No planning workflow was invoked, no plan was written, and
implementation has not begun. The preceding C-03/status update was committed as `27102355`; this final
approval record has not been committed.

### Fable review finding 1 approved: preserve nested Resource leaves

On 2026-11-07 the maintainer approved the Resource-leaf proposal after confirming that Resources already
support nesting beneath ORM ViewSets, that D-29 would remove that support, and that the proposal retains it.
The review evidence is the shipped Resource nesting documentation and list/detail parent-scoping tests.

The approved amendment is recorded as D-39 in the design:

- Resource leaves remain supported beneath one or more ORM ViewSets, in both cascade modes.
- Resources must be leaves: neither an ORM ViewSet nor another Resource may be nested beneath a Resource.
- Shared traversal resolves and authorizes the ORM ancestors and validates relationships between them before
  Resource loading. The Resource's existing `cv_get_items()` / `cv_get_item()` paths receive URL kwargs and
  remain responsible for restricting the collection/object to its URL parent.
- The framework does not independently verify Resource membership or add a generic Resource relationship
  validator. Top-level Resource behavior remains unchanged.

For example, Organization (ORM) → Publisher (ORM) → Files (Resource) is supported. Organization and Publisher
are checked by the shared mechanism; Files scopes its own data to Publisher and cannot have descendants.

D-39 supersedes D-29's blanket exclusion of nested Resources; the original decision remains recorded as
historical. Finding 1 is marked accepted in the
[Fable review](2026-11-07-ancestor-authorization-design-code-review-fable.md), with the original finding retained.
Findings 2–12 remain pending individual discussion. The design and review disposition were updated following
this approval; no plan, implementation, staging, or commit is authorized by it.

### Fable review finding 2 approved: document the core-parent permission migration

On 2026-11-07 the maintainer approved accepting finding 2 as a migration-documentation gap, with the planned
provider defaults unchanged. The discussion clarified that Guardian grants are attached to model objects
independently of the ViewSet class. Today a Guardian Book view can consume an object grant on its Publisher
even when Publisher is declared as a core ViewSet. The new traversal instead uses Publisher's own ancestor
provider, which defaults to model permissions for a core ViewSet.

The approved statement is recorded as D-40:

- Keep the planned defaults: core ViewSet ancestors use model permissions; GuardianViewSet ancestors use
  object permissions by default.
- Explicitly document that the old Guardian-child/core-parent combination changes from object-based to
  model-based parent checks, potentially removing or granting access.
- To retain object-based parent protection, migrate the parent to GuardianViewSet. Setting provider="guardian"
  on a core ViewSet remains invalid under C-02.
- Child-local permission checks remain independent. Add acceptance tests for the changed default and migration
  path when implementing the feature.
- Introduce no automatic compatibility translation or new mixed-composition warning.

The design's migration table, explanation, and acceptance criteria and the Fable review disposition were
updated. Original review findings remain intact. Findings 3–12 remain pending individual discussion; this
approval does not begin implementation or authorize a commit.

### Fable review finding 3 approved: separate ancestor and endpoint fallback

On 2026-11-07 the maintainer approved finding 3's migration and diagnostics clarification after asking whether
the view-level `cv_guardian_accept_global_perms` overrides the new ViewSet configuration. The approved answer
is that these settings control separate gates and have no default/override relationship.

For a Book request beneath a Guardian Publisher, Publisher's `ancestor_policy.accept_global_perms` controls
the Publisher ancestor gate. The Book view's `cv_guardian_accept_global_perms` controls its local Book gate
where applicable. Book's own ancestor fallback matters when Book is selected as an ancestor of a deeper
request, such as a Note; it does not configure Book's own endpoint checks.

D-41 records the resolution:

- Keep the planned independent settings and default False for Guardian ancestor fallback.
- Document that the child-view flag retains its endpoint-local role but loses its old parent-check role.
  An explicit ancestor-side fallback is needed when model-wide grants should satisfy a Guardian ancestor gate.
- Explain that ancestor fallback applies whenever that ancestor is selected across descendant endpoints,
  not only to the child view that previously enabled it. Migration is a deliberate shared-policy choice.
- Update manage diagnostics to distinguish the settings and remove applicability attributed solely to the
  old parent check. Preserve existing local/create semantics.
- Add acceptance coverage proving that neither setting relaxes the other gate and that the explicit migration
  and diagnostics reflect the approved scopes.

The design, review disposition, and discussion record were updated. Original review findings remain intact.
Findings 4–12 remain pending individual discussion. This approval covers documentation, not implementation
or a commit.

### Fable review finding 4 approved: explicit ancestor enforcement order

On 2026-11-07 the maintainer approved finding 4 as an integration-order clarification after discussing the
required order for a Book request beneath Publisher. Ancestor checks must succeed before the endpoint's own
permission checks, child loading, and action-state evaluation proceed. A denied Publisher must stop processing
without first looking up Book, building its form, evaluating its state, or performing writes.

D-42 records the approved statement:

- Enforce the already-approved B-03 ordering across all supported shipped view compositions. A check placed
  only in `CrudView.dispatch()` is insufficient because existing permission and object-processing code can
  execute earlier.
- Keep one shared authorization implementation. Small explicit integration bridges are acceptable if needed;
  their use must not duplicate authorization logic or create independent execution modes.
- Leave the precise hook to implementation planning, preserving existing local checks and supported denial
  responses. No particular `as_view()` or `setup()` solution is selected, and permission policy is unchanged.
- Require tests proving ancestor denial prevents downstream child lookup, state hooks, form/fragment processing,
  and writes, including the B-03 outer-denial/deeper-missing-object case.

The source review confirmed the dispatch ordering in representative plain, core permission-required, Guardian,
and manage compositions. Django ignores `setup()`'s return value, so returning a redirect there alone would
not stop dispatch. This technical correction is recorded without choosing the eventual integration mechanism.

The design, Fable review disposition, and discussion record were updated; original review findings remain
intact. Findings 5–12 remain pending individual discussion. Implementation and commits are not authorized by
this approval.

### Fable review finding 5 approved: preserve early actor denials for all-none chains

On 2026-11-07 the maintainer approved the proposed resolution for finding 5 and explicitly requested a commit.
The example was a Publisher with provider="none" and a Guardian Book endpoint requiring login. Under the
previous proposed ordering, an anonymous request could receive a login redirect for an existing Publisher
but a 404 for a missing one because relationship validation ran before the endpoint's own actor restriction.

D-43 records the approved refinement:

- Keep static configuration validation first.
- Before ancestor lookup, apply protected ancestry's actor policy where applicable and preserve the endpoint's
  existing early anonymous/inactive admission denials, including when all ancestors declare provider="none".
- Preserve the supported login/403/404 response without first checking ancestor existence or relationships.
- Add no login or inactive-user restriction to otherwise-public endpoints under all-none ancestry. A
  PermissionRequiredMixin alone does not imply mandatory login; supported permission-backend and manage
  behavior must be respected.
- Then resolve and authorize ancestry, followed by remaining child-local permission checks, child-object
  lookup, state hooks, forms/fragments, and writes. Passing early actor checks does not waive later gates.

This explicitly refines B-01/B-03 and D-42's ordering. It does not authorize moving the entire local permission
pipeline before ancestry, since that could load child objects or run state hooks prematurely. Acceptance
coverage must distinguish protected and public endpoints, compare valid/missing/mismatched ancestry for denied
actors, and prove no ancestor lookup occurs before an early denial.

The design, Fable review disposition, and discussion record were updated for the requested documentation
commit. Original review findings remain intact. Findings 6–12 remain pending; implementation is still deferred.

### Fable review finding 6 approved: validate before registration side effects

On 2026-11-07 the maintainer approved finding 6 and requested a documentation commit. The discussion clarified
that the registry is an in-memory directory of named ViewSets. If a new validation rejects construction after
`register()` has inserted the ViewSet and created its manage view, the rejected declaration can remain visible
and prevent a corrected declaration from using the same name.

A small isolated probe using the current construction path and a deliberately rejecting after-validator
confirmed the failure pattern: construction raised, the rejected ViewSet still had a registry entry and manage
view, and a valid replacement failed with an already-registered-name error. No production code or policy API
was implemented by the probe.

D-44 records the approved requirement:

- Validate new policy constraints that can be checked during construction before registering the ViewSet or
  creating its automatic manage view.
- Rejected construction must leave no registration behind; a corrected declaration can reuse the name.
- Checks that require completed registration, such as whether an action key exists, retain their later stage.
- Add acceptance tests proving clean rejection and successful retry.

Validation before registration is preferred over rollback machinery; the exact validator arrangement remains
an implementation choice. This changes no permission policy. The design, Fable review disposition, and
discussion record were updated for the requested commit, with the original review findings preserved.
Findings 7–12 remain pending; implementation is still deferred.

### Fable review finding 7 approved: nested manage retains normal ancestor checks

On 2026-11-07 the maintainer approved finding 7's clarification, requested a documentation commit, and asked
to continue with the next finding. The discussion distinguished the local manage gate from total access to a
nested manage page. Today local manage settings/group rules suffice; the planned Read classification adds
ancestor authorization and relationship validation to nested requests.

D-45 records the approved resolution:

- Retain the built-in manage Read classification and apply normal ancestor authorization and relationship
  validation to nested manage pages, including GuardianManageView.
- Preserve the existing manage-specific access rules as an additional independent gate. Manage settings or
  group membership do not bypass ancestor requirements.
- With all-none ancestry, add no ancestor login/permission requirement, but retain relationship validation and
  D-43's existing early actor restrictions. Top-level manage behavior remains unchanged.
- Document and test the nested access change. Do not introduce a special manage exemption or redesign the
  manage-specific access policy as part of diagnostics migration.

The design, Fable review disposition, and discussion record were updated for the requested commit. Original
findings remain intact. Findings 8–12 remain pending individual discussion; implementation remains deferred.

### Fable review finding 8 approved: built-in child redirects are reads

On 2026-11-07 the maintainer approved finding 8's resolution, requested a documentation commit, and asked
to continue with the next finding. The shipped RedirectChildView loads the current object and redirects to a
configured child endpoint; it does not itself mutate data, but was missing from the finite operation table.

D-46 records the approved resolution:

- Classify the built-in RedirectChildView family as Read. Nested requests use normal ancestor Read
  authorization and relationship validation without requiring an action entry merely for using this family.
- Preserve existing object lookup and any independent local checks, after ancestor enforcement.
- The destination independently enforces its own ancestor and local requirements on its request. A successful
  redirect does not grant access to the destination or determine the destination's operation classification.
- Retain explicit action overrides under the existing rules. Do not infer a classification for arbitrary
  redirects or custom actions; normal subclasses follow the existing built-in-family contract.
- Add the finite operation-table entry and acceptance coverage, including destination denial after a
  successful redirect and ancestor denial before redirect object lookup/processing.

The design, Fable review disposition, and discussion record were updated for the requested commit. Original
findings remain intact. Findings 9–12 remain pending individual discussion; implementation remains deferred.

### Fable review finding 9 approved: reject ineffective top-level request settings

On 2026-11-07 the maintainer approved finding 9's resolution, requested a documentation commit, and asked
to continue with the next finding. For Publisher → Book, Publisher has no ancestors, so its own request-side
settings cannot affect Publisher requests and are not inherited by Book. Allowing them could hide a policy
accidentally placed on Publisher instead of Book. Allowing unused settings would make policy reuse easier;
the approved choice is an error consistent with the existing rejection of ineffective configuration.

D-47 records the approved resolution:

- On a ViewSet without a parent, reject non-None cascade/read/write and nonempty actions. Both True and False
  cascade values are ineffective in this position, even if they match a global default.
- Keep None/empty defaults valid, whether omitted or explicitly supplied. Global request defaults remain valid
  and do not add ancestor checks to top-level requests. Top-level custom actions need no ancestor entry.
- Allow provider and accept_global_perms under their existing validation rules: they describe how this ViewSet
  is protected when it is an ancestor of a requested descendant.
- Identify the ineffective fields and explain that requirements for descendant requests belong on the
  requested descendant ViewSet. Reject before registration under D-44, without waiting for action registration
  or querying permission tables; require clean-rejection and corrected-name-retry coverage.

The design, Fable review disposition, and discussion record were updated for the requested commit. Original
findings remain intact. Findings 10–12 remain pending individual discussion; implementation remains deferred.

### Fable review finding 10 approved: exact registered keys for ancestor action overrides

On 2026-11-07 the maintainer approved finding 10's resolution, requested a documentation commit, and asked
to continue with the next finding. Existing navigation helpers resolve list to card when only card is
registered. The discussion distinguished that fallback from the exact key under which the endpoint is
registered. Applying the fallback to policy declarations could change an override's target when a real list
view is later added; exact keys keep the permission declaration tied to its endpoint.

D-48 records the approved resolution:

- Validate and resolve ancestor action overrides using exact registered view keys; do not apply navigation
  aliases to permission declarations.
- With only card registered, a card entry is valid and a list entry is an error. With both views registered,
  each entry configures only its own endpoint. A card view explicitly registered as list accepts that key.
- Preserve existing navigation aliases. A request reaching card through a navigation fallback uses card's
  own override, or its normal Read requirements when no override is supplied.
- Keep action entries optional for built-in list/card families, and preserve validation after completed
  registration. D-47 still rejects nonempty actions on a ViewSet without a parent.
- Require acceptance coverage for these registration cases, independent overrides, unchanged navigation
  fallback, and the built-in Read default.

The design, Fable review disposition, and discussion record were updated for the requested commit. Original
findings remain intact. Findings 11–12 remain pending individual discussion; implementation remains deferred.

### Fable review finding 11 approved: document the nested custom endpoint upgrade requirement

On 2026-11-07 the maintainer approved finding 11's migration-documentation clarification, requested a
documentation commit, and asked to continue with the next finding. The approved design already requires
ancestor_policy.actions entries for nested generic actions, custom forms, workflow views, and other endpoints
without a built-in classification. Existing applications must add these entries on upgrade, including core
applications that never used Guardian. The migration table had not explicitly identified that requirement.

D-49 records the approved resolution:

- Preserve the existing permission policy and document the explicit action-entry requirement as a breaking
  migration for core and Guardian applications in both cascade modes. Disabling cascade does not remove it.
- Add a migration-table row identifying affected endpoints, exact registered keys, complete nearest/higher
  permission pairs, and system-check/runtime configuration failures when entries are missing.
- Require the eventual feature's Breaking changelog entry and docs/migrating-1.0.md update to explain the
  declarations and failure behavior, including an example such as a custom Book.publish action under Publisher.
- Explain that built-in classified endpoints retain their effective defaults and top-level custom endpoints
  need no ancestor action declaration. Independent endpoint-local permissions remain in force.

The design, Fable review disposition, and discussion record were updated for the requested commit. Actual
release-document edits accompany implementation; this amendment records their requirements. Original findings
remain intact. Finding 12 remains pending individual discussion; implementation remains deferred.

### Fable review finding 12 approved: use the public ViewSet import in the example

On 2026-11-07 the maintainer approved finding 12's example-only cleanup and requested a documentation commit.
ParentViewSet is already exported from crud_views.lib.viewset, the approved public module for the new policy
types. D-50 updates the C-01 example to import AncestorPermissions, AncestorPolicy, ParentViewSet, and ViewSet
together from that module. The existing submodule import remains valid; this changes no permission or API
behavior.

The design, Fable review disposition, and discussion record were updated for the requested commit. All twelve
Fable findings now have approved dispositions, recorded in D-39–D-50, with the original review findings
preserved. Planning and implementation remain deferred.

### Astra review F-01 approved: ancestor ViewSet queryset and default-only database support

After completing the Fable review, the maintainer requested discussing the Astra findings before consolidating
the design into v2. F-01 concerns which queryset supplies ancestors and whether later parent consumers use the
same resolved identity. The initial proposal retained model-default-manager lookup and would not inherit
ancestor ViewSet filters. The maintainer questioned that behavior for soft deletion and tenant scoping,
noting that developers expect ViewSet restrictions to apply and may not read a documented exception.

The revised proposal uses the ancestor ViewSet's existing get_queryset method. Simple filters normally remain
part of the lookup query; complex joins, annotations, or prefetches retain their costs. The actual requested
child view supplies request and URL kwargs, while self is the ancestor ViewSet. No ancestor endpoint is
selected or dispatched. Reusing the resolved structural parent avoids a later model-based lookup disagreeing
with the object used during authorization.

The maintainer then requested skipping nondefault database support in wave one and approved the resulting
contract. D-51 records the resolution:

- Resolve each ORM ancestor through its ViewSet.get_queryset(view=requested_child_view), retaining its filters
  and validating the declared URL relationships. A filtered-out ancestor yields 404 when reached; never retry
  through an unfiltered manager. Preserve existing early-denial and traversal ordering.
- Pass the real requested endpoint, not a synthetic ancestor view. Its request/kwargs and child endpoint
  attributes retain their meaning. Ancestor view-specific queryset overrides are not invoked.
- Reuse the resolved immediate structural parent for create attachment, parent-based state checks, and supported
  request helpers. Model, PK, and database identity must agree; overrides substituting another parent are
  outside the supported contract. The structural parent need not be the nearest protected ancestor.
- Support only default for ORM ancestry, any ORM child data, and relevant authorization records in first-wave
  nested traversal. Explicit using("default") remains valid. A nondefault queryset or route is a configuration
  error; do not strip using(...) or silently redirect it to another database. Existing top-level database
  behavior and Resource-leaf application loading remain outside this restriction.

The design, Astra review disposition, and discussion record were updated. Original Astra findings remain
preserved. F-02/F-03 remain pending individual discussion before design-v2 consolidation. The maintainer
subsequently requested committing this documentation amendment and discussing F-02. Planning and implementation
remain deferred.

### Astra review F-02 approved: URL ancestry and mutation effects have separate boundaries

On 2026-11-07 the maintainer approved F-02's scope clarification, requested a documentation commit, and asked
to continue with the next finding. The discussion used two Guardian-protected publishers A and B, with Alice
authorized under A but not B and assumed to pass the endpoint-local checks. Editing a shared Genre through A
changes the same row seen through B. Likewise, a Book update form exposing its publisher FK can move the Book
from A to B after its original URL ancestry has passed. Neither full cascading nor D-51 queryset scoping
automatically authorizes those effects outside the URL path.

D-52 records the approved resolution:

- Ancestor authorization checks the declared URL ancestry. Additional authorization or constraints needed
  for shared-object writes, parent changes, and effects outside that path remain the endpoint/application's
  responsibility.
- Full cascading does not inspect every other related parent or guarantee isolation between containers.
  Existing endpoint-local checks remain independent; applications choose any additional protection required
  by their domain, such as restricting ordinary forms or explicitly authorizing moves/shared-object edits.
- Preserve standard save/delete semantics. Do not automatically pin an editable parent FK, add a destination
  gate, enumerate every membership, or turn deletion into unlinking. No generic mutation-policy engine is added.
- Document the shared-M2M and editable-parent-FK examples with their expected outcomes and application-owned
  constraints; carry the boundary into acceptance evidence for both cascade modes.

The design, Astra review disposition, and discussion record were updated for the requested commit. Original
Astra findings remain preserved. F-03 remains pending before design-v2 consolidation; planning and
implementation remain deferred.

### Astra review F-03 approved: ancestry validation must be safe before URL construction

On 2026-11-07 the maintainer approved F-03's validation-timing clarification and requested a documentation
commit. The discussion explained that URLconf import can access ViewSet.urlpatterns and enter a parent-chain
loop before a system check or request guard can reject a cycle. The maintainer asked about implementation
cost; a small metadata walk that detects repeated ViewSets and missing references provides a bounded solution.
The main integration work is consistent use across relevant parent-walking paths and forward-reference tests,
without database queries, a graph library, a persistent cache, or a new routing architecture.

D-53 records the approved resolution:

- Invalid ancestry must fail safely at or before URL construction can enter an unbounded walk. Keep the
  system-check and request safeguards as well; a late request-only check is insufficient.
- Cycles and missing parent references produce bounded, actionable configuration errors identifying the
  affected ViewSets or chain, using registration metadata without database queries.
- Preserve registration-order flexibility: a child may be declared before its parent, provided the reference
  resolves when URLs are constructed or the ancestry is otherwise needed.
- Reuse a small structural validation mechanism across relevant ancestry walks. The exact helper arrangement
  remains an implementation choice.
- Require acceptance coverage for self-cycles, two-ViewSet cycles, missing references, and valid forward
  references through actual urlpatterns/URLconf construction as well as the stated check/request paths.

The design, Astra review disposition, and discussion record were updated for the requested commit. All three
Astra findings now have approved dispositions in D-51–D-53, alongside the twelve resolved Fable findings.
Original review findings remain preserved. These decisions are ready for design-v2 consolidation; planning
and implementation remain deferred.

### Design v2 consolidation

On 2026-11-07, after approving all twelve Fable and all three Astra review resolutions, the maintainer requested
the design-v2 consolidation. The purpose is to give a fresh implementer or GSD planner one effective contract
without reconstructing the amendment history or asking again about settled decisions.

[Design v2](2026-11-07-ancestor-authorization-design-v2.md) now organizes the approved behavior by scope,
configuration, selection, operations, validation, request order, queryset/database identity, mutation boundary,
migration, implementation discretion, and acceptance evidence. Its traceability appendix maps every original
D-01–D-53 decision, identifying the Resource exclusion superseded by D-39 and distinguishing workflow/history
from implementation requirements. It adds no new product decision or D-ID.

The original design's body and the original reviews remain preserved. A banner marks the original design as
historical and directs readers to v2. The revised GSD handoff carries effective decisions with their source
IDs rather than mechanically promoting every historical ledger row into an implementation task. It separates
locked behavior, builder discretion, and deferred work. This editorial consolidation does not assign a phase
or authorize planning or implementation.
