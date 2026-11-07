# Ancestor authorization for nested ViewSets — design v2

Date: 2026-11-07. Status: canonical consolidation of approved decisions D-01–D-53; not implemented.
All twelve Fable findings and all three Astra findings have approved dispositions. This revision reorganizes
those decisions without adding behavior. Planning remains explicitly deferred; no phase is assigned.

## Status and GSD handoff

This document is the effective specification. Read its topic sections as the final contract, rather than
applying amendments from the original design in chronological order. The
[original design and decision ledger](2026-11-07-ancestor-authorization-design.md),
[discussion](2026-11-07-guardian-child-permissions-discussion.md),
[Fable review](2026-11-07-ancestor-authorization-design-code-review-fable.md), and
[Astra review](2026-11-07-guardian-child-permissions-design-review-astra.md) retain the reasoning and history.
The [traceability appendix](#decision-traceability) maps every original decision to its effective treatment.

For a future GSD discussion, research, or planning pass:

- Treat the effective behavior, API, scope, migration obligations, and acceptance requirements here as locked.
  Do not ask the maintainer to approve these choices again. Use original D-IDs as provenance when carrying
  effective decisions into `CONTEXT.md` and referencing them from tasks.
- Do not mechanically copy all 53 historical ledger rows into implementation decisions. D-29's Resource
  exclusion was amended, and workflow/history entries such as D-23 and D-38 are not executable feature tasks.
  Carry their current scope or authorization boundaries in the appropriate context section.
- Put this v2 document in canonical references. Separate locked decisions, builder discretion, and deferred
  work. The old design's instruction to copy its entire ledger is historical and is replaced by this handoff.
- Resolve ordinary implementation choices within [builder discretion](#implementation-guidance-and-discretion).
  If new code evidence exposes a genuine conflict, identify the affected effective rule and original D-ID;
  ask only about that conflict. Do not revive rejected alternatives as unanswered questions.
- Spec approval and this consolidation do not authorize a GSD workflow or implementation. Do not infer a
  phase from the current checkout. Wait for a separate instruction before creating phase or plan files.

Developer maintainability is a hard constraint alongside correctness: prefer a small, explainable mechanism,
preserve proven paths, and account for cognitive cost and additional queries. Public documentation must use
generic examples and omit identifying information from the separately reviewed application.

Sources: D-01, D-02, D-22–D-25, D-27, D-38.

## Scope and responsibility boundaries

One shared mechanism authorizes the ancestors of a requested nested endpoint. Both plain views and
permission-required views participate. The requested endpoint's own permission, queryset, state, and form
rules remain independent. A plain child may deliberately have no local permission gate while still requiring
ancestor permissions. No ancestor endpoint is selected or dispatched to infer its policy or run its state hooks.

| Configuration | Supported behavior in both cascade modes |
| --- | --- |
| ORM chain using declared `ParentViewSet` FK relationships | Validate the full URL relationship chain and enforce selected ancestor permissions |
| ORM chain using supported declared M2M metadata | Validate actual membership on the URL path and enforce selected permissions |
| ORM relationship not unambiguously expressible/validatable through existing metadata | Configuration error; no guessed relationship or exemption |
| Resource leaf under one or more ORM ViewSets | Authorize and validate ORM ancestry before existing Resource loading/scoping |
| Resource used as a parent of an ORM ViewSet or another Resource | Configuration error; Resources must be leaves |
| Top-level endpoint, including a Resource | Existing request behavior; no ancestor loading or permission queries |

For Organization → Publisher → Files, Files may be a Resource leaf. The shared mechanism resolves
Organization and Publisher and verifies their ORM relationship. The existing Resource `cv_get_items()` /
`cv_get_item()` contract receives URL kwargs; the application must restrict the collection/object to that
parent. The framework does not independently validate Resource membership or introduce a Resource relation API.
The operation, cascade, and failure-order rules still apply to a Resource endpoint, including a plain one.
Nothing may be nested beneath Files. This is the final Resource boundary; the original blanket exclusion is
superseded.

Authorization covers the declared URL path. It does not discover every related parent, authorize every effect
of a write, or guarantee isolation between containers. The [mutation boundary](#mutation-boundary) is part of
the supported contract, including for full cascade and M2M relationships.

Request enforcement is authoritative. Full ancestor-aware link/button visibility is deferred: a visible link
can lead to a denied destination. Existing helpers that consume removed policy fields must still receive the
bounded migration specified under [migration and diagnostics](#migration-and-diagnostics).

Sources: D-01–D-05, D-10, D-19, D-21, D-29 as amended by D-39, D-52.

## Public configuration

Export `AncestorPolicy` and `AncestorPermissions` from `crud_views.lib.viewset`.
`ViewSet.ancestor_policy` contains a fresh default `AncestorPolicy` per ViewSet. These are small typed
configuration values with validation, not permission evaluators or request handlers. Core must work without
Guardian installed; Guardian provider behavior belongs in its extension package.

`AncestorPermissions` has two required named string fields, `nearest` and `higher`. Each is a permission-map
key, resolved independently against the selected ancestor's map. A pair is always complete and replaces the
whole inherited pair; there is no partial merging or permission-skipping `None` sentinel.

| `AncestorPolicy` field | Default | Meaning |
| --- | --- | --- |
| `provider` | `None` | Owning class default; explicit choices are `"model"`, `"guardian"`, `"none"` |
| `accept_global_perms` | `False` | For a Guardian-protected ancestor, accept the required model permission as an alternative to its object permission |
| `cascade` | `None` | Requested ViewSet inherits global depth; explicit `True` / `False` overrides it |
| `read` | `None` | Inherit the global Read pair, or replace it with a complete `AncestorPermissions` |
| `write` | `None` | Inherit the global Write pair, or replace it with a complete `AncestorPermissions` |
| `actions` | Fresh empty dictionary | Exact registered view key → complete pair; overrides built-in requirements and is mandatory for unclassified nested operations |

The fields have two scopes:

- `provider` and `accept_global_perms` describe this ViewSet when it is used as an ancestor of a descendant.
- `cascade`, `read`, `write`, and `actions` describe requests targeting this ViewSet. They are not inherited
  from ancestor ViewSets. Requirements for Book requests belong on Book, even if Publisher is its parent.

`provider=None` means the class default, never unprotected. Only `provider="none"` removes that level's gate.
`cascade=False` still authorizes the nearest protected ancestor. `read=None` and `write=None` mean inheritance.
Changing an ancestor provider does not change the registered views' endpoint-local permission behavior.

Django settings supply these defaults:

```python
CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE = True
CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS = {"nearest": "view", "higher": "view"}
CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS = {"nearest": "change", "higher": "view"}
```

Validate both mappings as complete pairs; settings need no import from the ViewSet module. There is no global
provider, Guardian fallback, or action-key map, and no new per-view traversal configuration in this wave.
Do not mutate declarations while resolving them or store request/user/object/grant state in either type.

The following is the approved future API, not an API implemented by this documentation change. Application
model imports are omitted. `ParentViewSet` is already exported from the same public module.

```python
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet

customers = GuardianViewSet(model=Customer, name="customer")
addresses = ViewSet(
    model=Address,
    name="address",
    parent=ParentViewSet(name="customer"),
    ancestor_policy=AncestorPolicy(provider="none"),
)
```

A write to Address requires Customer change by default. Address's `none` provider matters when Address is an
ancestor of a deeper endpoint; it does not disable traversal on Address requests. Actual relationship names
must match `ParentViewSet` metadata. Independent alternative declarations are:

```python
# On a nested ViewSet: retain its provider and select only the nearest protected ancestor.
AncestorPolicy(cascade=False)

# On a nested ViewSet: require change on every selected protected ancestor for writes.
AncestorPolicy(write=AncestorPermissions(nearest="change", higher="change"))

# On a nested ViewSet with an actual registered "approve" endpoint.
AncestorPolicy(actions={"approve": AncestorPermissions(nearest="change", higher="view")})

# On a GuardianViewSet: allow model grants when this ViewSet is checked as an ancestor.
AncestorPolicy(accept_global_perms=True)
```

Sources: D-06, D-07, D-14, D-16–D-18, D-26, D-33, D-35–D-37, D-41, D-47, D-48, D-50.

## Provider and cascade selection

Determine protected levels from configuration, independently of the actor's grants. Resolve required keys
through each selected ancestor's permission map. Core ancestors default to model permissions; Guardian
ancestors default to strict object permissions. An intentionally unprotected level must declare `"none"`,
even when all its own endpoints are plain.

| Ancestor declaration | Gate | Protected position |
| --- | --- | --- |
| Core class default, or explicit `"model"` | Required model permission | Counts as protected |
| Guardian class default, or valid explicit `"guardian"` | Required permission on the resolved object | Counts as protected |
| Explicit `"none"` | No local permission check | Pass through; does not consume the nearest-protected position |
| Invalid provider or missing required key | Configuration error | Never reinterpret as unprotected or try a weaker permission |

Guardian uses its configured content-type semantics and direct/group object grants. With ancestor
`accept_global_perms=True`, a model grant OR the required object grant satisfies that ancestor gate. This is
independent of the endpoint view's `cv_guardian_accept_global_perms`; neither supplies a default or override
for the other. Protected providers deny inactive authenticated actors and preserve normal backend superuser
semantics. `none` introduces no local actor-permission gate.

For an ordinary active authenticated actor, on the correct object:

| Required object grant, direct or group | Required model grant | Fallback off | Fallback on |
| --- | --- | --- | --- |
| No | No | Deny | Deny |
| Yes | No | Satisfy this gate | Satisfy this gate |
| No | Yes | Deny | Satisfy this gate |
| Yes | Yes | Satisfy this gate | Satisfy this gate |

The requested ViewSet's explicit cascade overrides the global value in either direction. An ancestor's own
cascade value cannot stop a descendant's traversal. There is one mechanism with two depths:

| Global | Requested ViewSet | Selected permission gates |
| --- | --- | --- |
| `True` | `None` or `True` | All protected ancestors |
| `True` | `False` | Nearest protected ancestor only |
| `False` | `None` or `False` | Nearest protected ancestor only |
| `False` | `True` | All protected ancestors |

Both modes resolve the full declared ancestry and validate all supported relationships, including at `none`
levels and during create. Nearest-only skips higher permission evaluation, not their scoped existence and
relationship checks. Denial at the nearest protected gate ends authorization; it never tries a farther
ancestor as an alternative. All-none ancestry has no ancestor permission gate but retains relationship and
endpoint-local checks. There is no total opt-out, second legacy execution mode, or invented child-add fallback.

Sources: D-03, D-06–D-10, D-15, D-18, D-20, D-21, D-26, D-41.

## Operation requirements

| Effective operation pair | Nearest protected ancestor, either mode | Higher protected ancestors, full cascade only |
| --- | --- | --- |
| Read default | `view` | `view` |
| Write default | `change` | `view` |
| Example stricter Write override | `change` | `change` |
| Example more permissive Write override | `view` | `view` |

These are ancestor requirements, independent of the endpoint's own permission. Deleting a child requires
parent `change` by default, not parent `delete`. Opening a create/update/delete form is already a Write
operation; the HTTP method does not determine classification.

Use a finite classification of shipped families, including their normal subclasses and permission variants:

| Endpoint family | Ancestor classification |
| --- | --- |
| Core list/card/detail, rich ObjectDetail, polymorphic detail | Read |
| Core create/update/delete and polymorphic variants | Write, including form/confirmation GET |
| Polymorphic create-type selection | Write |
| Built-in ordered up/down actions | Write |
| Built-in `RedirectChildView` | Read |
| Built-in core and Guardian manage | Read; independent local manage gate remains |
| Generic `ActionView`, object/no-object custom forms, workflow, other custom endpoints | Explicit action pair required when nested |
| Formset fragment request | Same operation and requirements as its owning editor |

An exact registered action entry replaces the family/default pair. It cannot disable traversal. Renaming a
standard CRUD view's `cv_key` preserves its family. Naming a generic action `detail`, or setting its local
`cv_permission="view"`, does not classify it as Read. A custom override changing a standard family's semantics
must supply an explicit action pair; the framework does not inspect method bodies. Missing custom declarations
are errors in both cascade modes, even with all-none ancestry. Top-level custom endpoints need no entry.
No extensible operation registry is required.

Action validation and override selection use literal registration, not navigation aliases:

| Registered endpoints on the nested ViewSet | Action behavior |
| --- | --- |
| Only `card` | `actions["card"]` is valid; `actions["list"]` is an error |
| Both `list` and `card` | Each entry affects only its own endpoint |
| `CardListView` actually registered as `list` | `actions["list"]` is valid; the built-in family remains Read |
| Built-in list/card without an override | Use the effective Read pair |

Preserve navigation's existing `list` → `card` fallback. A request reaching Card through it still uses Card's
actual registered key, never another endpoint's policy entry. Check key existence after registration completes.

Nested manage requests must pass normal ancestry checks AND the existing manage settings/group gate. Public
manage settings or manage-group membership cannot bypass selected ancestors or relationships. All-none
ancestry retains early actor rules and the local manage gate. Top-level manage behavior remains unchanged.

`RedirectChildView` needs no declaration merely because it redirects. Its ancestry checks precede its object
lookup and redirect processing, while local checks remain. The destination request independently authorizes
its own operation, ancestors, and local permissions. An explicit action pair may override this built-in Read
pair; arbitrary custom redirects do not acquire the classification automatically.

For Organization → Customer → Address (`none`) → Instruction, with the other ancestors protected:

| Level | Read, full cascade | Write, full cascade | Read, nearest-only | Write, nearest-only |
| --- | --- | --- | --- | --- |
| Organization | `view` | `view` | No permission evaluation | No permission evaluation |
| Customer | `view` | `change` | `view` | `change` |
| Address | No local gate | No local gate | No local gate | No local gate |
| Instruction endpoint | Own checks | Own checks | Own checks | Own checks |

Every column still requires valid ancestry. A `change/change` Write pair changes Organization's full-cascade
requirement to `change`; nearest-only still omits its permission evaluation.

Sources: D-05, D-11–D-17, D-27, D-31, D-45, D-46, D-48, D-49.

## Validation and safe ancestry construction

Validate static configuration without querying model, ContentType, Permission, or grant tables. Resolve
database-backed permission vocabulary only at a reached selected gate during request enforcement.

| Invalid declaration or situation | Required failure and timing |
| --- | --- |
| Unknown policy/pair field or provider | Structural validation error; do not ignore it |
| Non-boolean `accept_global_perms`, or `cascade` other than a boolean or `None` | Reject without coercion; validate global cascade equivalently |
| Empty or whitespace-padded permission key, incomplete pair, `None` component or action pair | Structural validation error; no skipping or partial merging |
| Explicit global Read/Write mapping missing either field | Structural validation error; only an omitted setting uses its default pair |
| `provider="guardian"` on core `ViewSet` | Construction error directing the developer to `GuardianViewSet` |
| `accept_global_perms=True` with effective provider other than Guardian | Construction error for an ineffective flag; explicit `False` remains valid |
| No parent, but non-`None` cascade/read/write or nonempty actions | Construction error naming the ineffective request fields |
| Explicit removed Guardian parent-policy declaration | Construction error, including a subclass declaration or an explicit old default/`None` |
| Action key not literally registered | Completed-registry system-check error and runtime guard; do not reject a still-incomplete nested registry |
| Unclassified nested endpoint without its action pair | System-check error and runtime guard, including all-none ancestry |
| Unsupported relationship or Resource ancestor | System-check error and runtime guard in either mode |
| Cycle or unresolved parent at URL construction or another supported ancestry walk | Bounded configuration error before an unbounded walk; identify affected ViewSets/chain |
| Required key absent from a reached selected ancestor's permission map | Runtime `ImproperlyConfigured`; no weaker fallback |
| Reached nondefault database selection on a supported nested ORM/auth path | Configuration error under the database contract below; no rerouting |

Use existing Pydantic `ValidationError` style for construction-time structural/owning-ViewSet validation.
Cross-ViewSet, completed-registry, and relationship failures have Django system-check errors plus
`ImproperlyConfigured` guards where URL construction or requests need the structure. Configuration messages
identify the ViewSet, action where relevant, and offending field/key/chain, without request/user/grant state.
A database failure is an error, never a permission success.

On a top-level ViewSet, omitted or explicit `cascade=None`, `read=None`, `write=None`, and `actions={}` are valid.
Both explicit cascade booleans and explicit pairs matching the global defaults are rejected there. Provider
and Guardian fallback remain meaningful when that ViewSet is an ancestor; their ordinary validation applies.
Global defaults do not invalidate top-level ViewSets or create ancestry. A standalone policy may contain
request settings for subsequent use with a nested ViewSet.

Every new constraint decidable during ViewSet construction must run before registry insertion and automatic
manage-view creation. Failed declarations leave no entry or automatic manage view; existing entries remain
intact and a corrected declaration may reuse the name. This includes owning-class/provider/fallback errors,
ineffective top-level request settings, and explicitly removed fields. Prefer validation before registration
over rollback. Later action-key existence checks and cross-ViewSet forward references retain their later stage.

A child may be constructed before its parent is registered. The reference must resolve when its URLs are
constructed or ancestry is otherwise needed. Validate cycles and missing references at or before URL-building
walks, because URLconf import may precede system checks and request dispatch. Other supported ancestry walkers
must also terminate safely. Keep system-check and request safeguards; a late guard alone is insufficient.
Use a small shared metadata walk, without a graph library, persistent ancestry cache, or replacement router.

Sources: D-07, D-17, D-28, D-29/D-39, D-33, D-36, D-44, D-47, D-48, D-51, D-53.

## Request order and denial behavior

URL construction first satisfies the structural safety contract above. For a nested request, use this order
in every supported shipped composition:

1. Validate static policy, operation, and ancestry declarations. Resolve effective depth and operation pair;
   select protected levels from configuration before object lookups. No permission-table queries here.
2. Apply the selected ancestry's actor policy and preserve the endpoint's existing early anonymous/inactive
   admission denials, even for all-none ancestry. Do not load children or invoke state hooks to discover an
   actor decision. Do not add actor restrictions to otherwise-public all-none endpoints.
3. Resolve one ancestor at a time, outermost inward, through its ViewSet queryset. Validate its existence and
   relationship to the already resolved chain. Missing/excluded objects or mismatched relationships yield 404
   when reached. Do this at protected and `none` levels in either cascade mode.
4. Immediately after validating each ancestor selected for permission evaluation, resolve its required key
   and check that gate, before processing the next level. Invalid key is a configuration error; denied active
   authenticated actor receives 403. Stop at the first reached failure.
5. After ancestry succeeds, continue remaining endpoint-local permissions, child queryset/object loading,
   action-state handling, forms/fragments, and writes through their existing paths. Do not dispatch ancestor
   endpoints or run their state hooks. Resource leaf loading occurs at this stage.

Steps 3 and 4 are interleaved; do not load the entire chain before evaluating its selected gates. In
nearest-only mode, higher ancestors are still resolved and relationships validated, without evaluating their
permissions. Top-level endpoints keep their existing request path and perform no ancestor work.

| Actor and ancestry | Response contract before ancestor lookup |
| --- | --- |
| Anonymous, at least one protected ancestor | Requested endpoint's supported anonymous/no-permission response; default login redirect if none configured |
| Anonymous Guardian endpoint configured for 403/404, protected ancestry | Preserve that configured response |
| Authenticated inactive actor, protected ancestry | 403 regardless of grants, including inactive superusers |
| All-none ancestry, existing endpoint early rules reject the actor | Preserve its supported login/403/404 denial before any ancestor lookup |
| All-none ancestry, endpoint permits the actor | Add no login/inactivity restriction; continue relationship and later local checks |

An active authenticated actor denied at a selected ancestor gate gets 403, not a login redirect. Plain views
without `AccessMixin` still need the default login response for protected ancestry. Do not consult ancestor
endpoints' response preferences or add per-view traversal flags.

`PermissionRequiredMixin` inheritance alone does not prove login is required: supported core backends or
manage settings can permit anonymous access. Preserve actual existing actor admission. A full local
`has_permission()` call that loads the child or checks action state cannot serve as the early actor phase.
Other endpoint-local denial behavior remains independent after ancestry succeeds.

| Competing conditions, after valid static configuration | First reached result |
| --- | --- |
| Protected ancestry, anonymous actor, nonexistent parent PK | Endpoint login/denial response without parent lookup |
| All-none ancestry, existing early actor denial, valid/missing/mismatched parent | Same early denial for all three; no ancestor lookup |
| All-none ancestry, actor permitted, reached missing/mismatched parent | 404 |
| Full cascade: outer selected gate denies; deeper ancestor is missing | 403 without probing the deeper ancestor or calling its queryset |
| Earlier gates pass; next ancestor is excluded, missing, or mismatched | 404 |
| Nearest-only: higher grant absent, all relationships valid, nearest gate passes | Continue local checks; no higher permission evaluation |
| Reached selected gate names a missing permission key | Configuration error |

Ancestor and local permissions compose as independent gates: any required denial denies; satisfying ancestry
does not waive a local gate, and local success does not waive ancestry. Satisfying permission gates does not
guarantee a successful response; existence, state, and form validity still matter.

Sources: D-03–D-05, D-10, D-15, D-30, D-32, D-42, D-43, D-51.

## Ancestor querysets, identity, and databases

The ancestor ViewSet's queryset is authoritative for ancestor visibility. Call
`ancestor_viewset.get_queryset(view=requested_child_view)` and resolve that ancestor's declared URL PK within
the result. Preserve its manager and ViewSet filters, including soft deletion or tenant scope. Always validate
declared relationships as well; a queryset override does not waive them. An excluded row produces 404 when
reached even if the actor holds a grant; never retry through an unfiltered manager.

| Input or consumer | Contract |
| --- | --- |
| `self` inside `get_queryset` | The ancestor ViewSet being resolved |
| `view` argument | Actual requested endpoint, with unchanged request and URL kwargs; its model, `cv_key`, and any leaf `pk` still describe the child |
| Ancestor identity lookup | Use that ancestor's configured URL argument, not the child's leaf `pk` or a guessed argument name |
| Ancestor list/detail view queryset overrides and permission mixins | Not invoked or inherited; the ViewSet queryset and explicit ancestor provider apply separately |
| Create attachment, parent-based state checks, supported request helpers | Reuse the resolved immediate structural parent with the same model/PK/database identity |
| Custom parent loader substituting another object/database | Outside the supported contract |

These rules apply to `none` ancestors and nearest-only traversal too. Preserve early actor and interleaved
failure ordering: no ancestor queryset call before an applicable early actor denial, and no deeper queryset
call after an earlier gate denies. Querysets using `view.request.user` receive the current actor; overrides
must account for the actual child endpoint context, not a synthetic ancestor view.

The immediate structural parent remains the parent used for FK/M2M attachment and state checks even when it
is unprotected and a farther ancestor supplies the nearest permission gate. Migrate shipped
`cv_get_parent_object()` request consumers to reuse this resolved object; do not retain a second unfiltered
resolution path. No new public loader API, dispatched ancestor view, or persistent object cache is introduced.

Wave one supports only `default` for the new nested traversal's ORM ancestors, any ORM child data, and
relevant authorization records. A nondefault queryset or router selection is a configuration error when
reached under normal ordering. Preserve the selection long enough to validate it: never strip `.using(...)`,
force `.using("default")`, or silently query a different copy of the row. Explicit `.using("default")` is valid.
Nondefault traversal, cross-database ancestry, and central-auth/sharded-data arrangements are unsupported.
Existing top-level database behavior is unchanged. Resource leaf application loading remains its existing
contract; its ORM ancestry and relevant authorization records follow this default-database rule.

Source: D-51, with the relationship and ordering contracts from D-10, D-32, D-39, D-43.

## Mutation boundary

Passing ancestry authorizes the declared URL path. Additional restrictions required by a domain for shared
objects, reparenting, or custom effects belong to the endpoint/application. Existing endpoint-local gates
remain independent. The following outcomes assume valid URL ancestry, all required gates passed, a valid
operation/form, and no additional application restriction:

| Operation | Outcome and responsibility |
| --- | --- |
| Update Genre shared by Publishers A and B through A | The shared row changes for both. B is outside the path and receives no automatic permission check |
| Update Book through Publisher A with an editable publisher FK changed to B | The valid form can move Book to B. Original membership under A neither authorizes B nor causes an automatic destination gate or FK pin |
| Delete an object shared with another parent | Normal deletion semantics; nesting does not turn deletion into unlinking from A |
| Custom action affects other objects/parents | Its declared pair covers URL ancestry; the action owns any extra authorization required for its effects |

Applications can omit the parent field from ordinary forms, authorize a separate move operation, or protect
shared edits with suitable object permissions/domain rules. These are examples of application choices, not
automatic framework restrictions. Ancestor queryset scoping does not validate every submitted relationship
or effect. Full cascade means higher ancestors on the same URL path, not all memberships or container
isolation. No generic mutation-policy engine is introduced. Document and test this boundary in both modes.

Source: D-52; related D-10, D-39, D-51.

## Migration and diagnostics

The maintainer controls the downstream migration. Make the breaking change explicit and direct; do not keep
two ancestor implementations, silently translate legacy declarations, or invent a child model-add gate when
cascade is off. Preserve existing child-object checks, Guardian list filtering, authentication/inactive rules,
action-state gates, nested create semantics, and applicable local view options.

| Existing configuration/behavior | Required migration |
| --- | --- |
| `cv_guardian_parent_permission` or `cv_guardian_parent_create_permission` | Remove both policy fields and replace ancestor enforcement with the shared mechanism; reject explicit constructor/subclass declarations even when `None` or equal to an old default |
| Old create override `None` | Previously inherited the old ordinary-parent key; do not reinterpret it as new provider `none` or silently translate it |
| Old parent key `None` | Previously skipped that permission check while retaining parent/state processing; migrate deliberately to the new policy scopes, without removing actor/state gates |
| Nearest-only mode | New mechanism still enforces nearest protected ancestry; it is not legacy behavior or a total disable switch |
| Nested custom endpoints, core and Guardian | Add exact registered action keys with complete pairs; missing declarations fail checks/runtime in both modes |
| Guardian child under a core parent | Parent gate now uses core model permissions; use a `GuardianViewSet` parent to retain object-based ancestor protection |
| Child view `cv_guardian_accept_global_perms` previously affected parent gate | It retains only applicable endpoint-local behavior; explicitly choose ancestor fallback on the ancestor ViewSet |
| Nested manage endpoint | Existing manage gate remains; normal ancestry authorization and relationships are additional requirements |
| Ancestor scoping | Put shared visibility restrictions in ancestor ViewSet `get_queryset`; individual ancestor endpoint queryset overrides are not inherited |
| Nested nondefault ORM/auth routing | Unsupported in wave one; configuration error when reached, with no silent default-database fallback |
| Visible links/buttons | May lead to newly denied requests; only bounded migration of existing immediate-parent checks is included |

Remove the old framework field defaults without treating their mere previous existence as an explicit user
declaration. Reject actual constructor/subclass use so mistakes cannot be silently ignored. The child view's
local `cv_guardian_accept_global_perms` remains supported; do not reintroduce the already removed ambiguous
ViewSet-level field of that name.

### Core parent and Guardian child

Previously a Guardian child could check a parent object grant even if its parent was a core ViewSet. Under
the final defaults, a core Publisher parent requires a model grant; a Guardian Publisher parent requires an
object grant by default. Assuming other gates pass:

| Grant on Publisher | New default core parent gate | Default Guardian parent gate |
| --- | --- | --- |
| Object grant only | Deny | Satisfy |
| Model grant only | Satisfy | Deny |

This can remove or grant access during migration. To retain object-based parent protection, change the parent
to `GuardianViewSet`; `provider="guardian"` on a core ViewSet remains invalid because Guardian supplies its
permission-map/content-type semantics. No compatibility translation or new mixed-composition warning is added.
Independent child allow/deny cases remain independent.

### Independent global-permission fallback

For Guardian Publisher → Guardian Book, the Publisher ancestor's `AncestorPolicy.accept_global_perms` controls
Publisher fallback across every descendant request selecting it. The Book view's
`cv_guardian_accept_global_perms` controls its own applicable local gate. Enabling Book's view flag cannot
relax strict Publisher ancestry; enabling Publisher fallback cannot relax a strict Book object gate.

A model-only Publisher grant that formerly passed because Book's view flag was enabled can now deny until
Publisher explicitly enables ancestor fallback. That change affects all descendant endpoints selecting
Publisher, so migration requires a deliberate shared-policy choice; do not automatically copy a child flag.
Book's own `AncestorPolicy.accept_global_perms` matters when Book is an ancestor of a deeper endpoint, such as
Note. It does not control the Book view's local gate. Nested Guardian create gains no new model-add fallback;
report only remaining local applicability for its view flag.

### Custom endpoint declaration example

For a registered nested custom endpoint with `cv_key="approve"`, add to its owning ViewSet:

```python
from crud_views.lib.viewset import AncestorPermissions, AncestorPolicy

policy = AncestorPolicy(
    actions={"approve": AncestorPermissions(nearest="change", higher="view")},
)
```

Supply it as that nested ViewSet's `ancestor_policy`, retaining any other required policy choices. Both fields
are required; use the actual registered key. Built-in classified endpoints need no entry unless overriding
their pair. Top-level custom endpoints need no entry, and top-level nonempty `actions` is rejected.

### Existing helper consumers

| Existing helper/diagnostic situation | Bounded migration |
| --- | --- |
| Already checks a resolved immediate structural parent | Use that parent's provider/fallback and the target operation's nearest requirement |
| Immediate structural parent has provider `none` | Skip that local gate, retain actor/state/custom denials; do not traverse farther for rendering |
| Supported inputs cannot establish required parent context | Retain existing unavailable/`False` behavior; do not invent a parent |
| Invalid configuration | Surface the error; do not grant access or silently hide the mistake |
| Manage displays removed fields | Show declared policy, cascade, requirements, and ancestor fallback separately from local Guardian options |
| Manage reports view fallback applicability | Report only remaining local applicability, without implying a default/override relation to ancestor fallback |

Existing supported single-FK child inputs may still establish a structural parent. Ambiguous child-only M2M
inputs must not guess one. During a supported nested request, reuse the resolved parent identity under D-51.
Outside that request, these helpers may perform their existing immediate-parent resolution, without new
full-chain navigation queries. A `none` immediate parent can leave a visible button whose request later fails
at a farther protected ancestor; that is within the first-wave UI limitation. Configuration display does not
prove user access to a chain.

During implementation, update feature/configuration/Guardian/manage guidance and examples. The feature's
`### Breaking` changelog entry and `docs/migrating-1.0.md` must explain the removed fields, provider-default
change, independent fallback scopes, nested custom declarations, and added nested-manage requirements.
Document queryset/default-database and mutation boundaries, Resource scoping, and link-visibility limitations.
This consolidation itself does not create a release entry for unimplemented behavior.

Sources: D-19, D-21, D-22, D-28, D-34, D-40, D-41, D-45, D-49–D-52.

## Implementation guidance and discretion

The integration must be understandable and traceable. Keep one shared ancestor implementation and a small
explicit provider boundary; no public arbitrary backend registry. Small explicit integration bridges may be
needed to preserve the request order. The builder chooses their private layout and lifecycle entry points
after inspecting supported MROs, without changing the contract or asking again about settled policy.

| Existing source / integration area | Constraint to account for |
| --- | --- |
| [ViewSet](../../src/crud_views/lib/viewset/__init__.py), [ParentViewSet](../../src/crud_views/lib/viewset/parentviewset.py) | Registry name, relationship attribute, and URL PK argument are distinct; respect explicit FK/M2M metadata and int/UUID PKs. `register()` has side effects; validate new decidable constraints first |
| ViewSet ancestry/URL helpers | Audit `get_parent_url_args`, `get_parent_attributes`, `get_path_parent`, `urlpatterns`, and related walks for safe termination; preserve valid forward references |
| [Core view base](../../src/crud_views/lib/view/base.py) | Preserve cancel-restore/modal dispatch work, local permissions, and action-state responsibility. Replace supported request parent re-resolution with the traversal result |
| Core permission-required and manage MROs | Django permission dispatch can run before `CrudView.dispatch()` and invoke child lookup/state. A guard only in `CrudView.dispatch()` is insufficient |
| Django lifecycle | `as_view()` ignores the return value of `setup()`; merely returning a redirect there cannot short-circuit a request. No specific wrapper/hook has been approved |
| [Guardian mixins](../../src/crud_views_guardian/lib/mixins.py), [views](../../src/crud_views_guardian/lib/views.py) | Replace only the ancestor portion of the old parent gate; preserve object gates, list filtering, groups, inactive actors, create state, and supported composition guards |
| [Guardian ViewSet](../../src/crud_views_guardian/lib/viewset.py) | Preserve `guardian.ctypes.get_content_type` semantics and strict `get_objects_for_user()` helper behavior; ancestor fallback does not change existing helper/local contracts |
| [Create](../../src/crud_views/lib/views/create.py), [form processing](../../src/crud_views/lib/views/mixins.py) | Attach the actual structural parent through configured FK/M2M metadata and existing through defaults; gate before hooks, forms, saves, and commit callbacks |
| [Formset mixins](../../src/crud_views/lib/formsets/mixins.py), [formsets](../../src/crud_views/lib/formsets/formsets.py) | Fragments can load `self.object` before rendering; guard before that. Fragment-coordinate checks remain distinct from URL ancestry |
| [Card](../../src/crud_views/lib/views/card.py), [polymorphic selection](../../src/crud_views_polymorphic/lib/create_select.py), [child redirect](../../src/crud_views/lib/views/child.py) | Explicitly include their approved families; Card and polymorphic selection do not inherit the corresponding core List/Create class |
| [Resource](../../src/crud_views/lib/resource.py) | Preserve Resource mixin composition and application-owned kwargs scoping; no Resource ancestor or generic membership API |
| [Settings](../../src/crud_views/lib/settings.py) | Follow the existing deliberate settings-capture pattern; tests may need to patch the singleton rather than assume `override_settings` refreshes it |
| [Core checks](../../src/crud_views/checks.py), [check infrastructure](../../src/crud_views/lib/check.py), [Guardian checks](../../src/crud_views_guardian/checks.py) | Choose unused IDs, retain runtime safeguards, keep checks migration-safe, and do not broaden unknown-attribute exemptions to hide mistakes |

Before removal, search every consumer of the old parent fields and helpers: collection links, contextual create
buttons, `cv_create_has_access`, cancel availability, Guardian composition checks (`crud_views_guardian.E001`),
manage data/applicability reporting, and
[the Guardian configuration template](../../src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html).
Apply the bounded helper contract; request-only scope does not permit dangling field accesses.

Do not weaken Guardian child-object/queryset composition checks to accommodate plain endpoints. Shared
ancestor enforcement can support a plain child while Guardian permission-required families retain their local
protections. Existing nested Guardian create intentionally lacks a separate model-add requirement; top-level
create retains its local requirement. Preserve parent-based create state even where old permission keys were
`None`. Model fallback requires the separate model check plus object check; passing an object to Django's
model backend does not itself provide that fallback.

Custom overrides must cooperate with the documented entry point. Arbitrary dispatch code bypassing it and
parent loaders substituting another identity are unsupported; checks may catch known bad compositions but
must not claim to verify arbitrary method bodies.

Builder discretion includes private modules, validator arrangement, finite family-recognition mechanics,
small shared walk/provider helpers, request-local storage, test organization, and actionable check IDs/messages
within the specified contracts. It does not include changing defaults, scope, supported relationships,
queryset context, database support, failure order, operation classifications, or migration semantics.

### Performance and caching

Use request-local state. Reuse resolved ancestors and provider checkers where practical and avoid duplicate
identical ancestor checks; local gates remain independent even if they require separate queries. No persistent
authorization-result or object cache is introduced. Existing permission-vocabulary caching is distinct from
caching user access. Revocation must take effect on the next request.

Measure one- and three-level chains against the current baseline in both modes, covering representative plain
and Guardian list, object, and create requests. Record query differences and explain repeated resolution/checks;
do not promise zero overhead or impose an unmeasured fixed cross-backend budget. Top-level requests must do no
ancestor work. Nearest-only must perform no higher permission evaluations, while its relationship/visibility
reads remain necessary. Cascade depth is a cost control, not a claim that traversal becomes free.

Sources: D-02, D-03, D-16, D-20–D-22, D-25, D-31–D-34, D-36, D-42–D-44, D-48, D-51, D-53.

## Acceptance requirements

The following evidence is required during implementation. These are observable boundaries, not prescriptions
to write tests mirroring internal helpers. Run appropriate repository checks and framework coverage; use
bounded multicore pytest for broad runs. This documentation revision does not implement or test the feature.

| Area | Required evidence |
| --- | --- |
| Independent gates | Guardian ancestor denial cannot be bypassed by a plain child or global child grant; local child denial still denies after ancestor success; deliberately absent child gate is supported |
| Selection and precedence | Full and nearest-only modes, both global/ViewSet override directions, ancestor cascade unable to stop descendants, none-middle and all-none chains; denied nearest never tries farther grants |
| Requirements | Default Read/Write, create/update/delete GET as Write, configurable `change/change` and `view/view`, deletion using parent change, exact action overrides |
| Finite families | Every listed family, permission variant, normal subclass and renamed key; Card, polymorphic selection, ordered actions, rich detail, owning-editor fragments, and misleading generic keys |
| Custom declarations | Missing entries fail checks and runtime for core/Guardian in both modes, including all-none; complete entries work; top-level custom actions need no entry |
| Actor and provider behavior | Anonymous default redirect and configured 403/404, inactive actors including superusers, active superusers, group grants, model provider, strict Guardian and explicit fallback |
| Early actor order | All-none chains with existing actor denial return the same supported result for valid/missing/mismatched ancestry without ancestor lookup. Public plain and supported anonymous-permitting backend/manage paths gain no login requirement |
| Interleaved enforcement | Outer permission denial prevents deeper lookup/queryset calls, even when deeper data is missing. Observe execution order across plain, core permission-required, Guardian, manage, Resource and extension compositions |
| Downstream work | Reached ancestor denial prevents remaining local permission work, child lookup, state hooks, Resource loaders, form/fragment processing, side effects and writes; success still reaches independent local gates |
| Relationships and creates | Int/UUID PKs, explicit URL/FK names, multi-level mismatch/404 including create before attachment; supported M2M membership; structural parent remains distinct from nearest protected ancestor |
| Resource leaves | Existing list/detail scoping under one/multiple ORM ancestors in both modes, independent local gates and application membership; Resource ancestors fail clearly; top-level behavior unchanged |
| Queryset scope | Soft-delete/tenant/manager exclusions despite a valid grant, no unfiltered retry, both modes and none ancestors, actual child view/request/kwargs, ancestor endpoint queryset overrides not invoked |
| Parent identity | Create attachment, state checks and supported request helpers reuse the same resolved model/PK/database identity, including a none immediate parent |
| Database boundary | Default and explicit `.using("default")` work; reached nondefault queryset/router selections for nested ORM/auth paths fail without rerouting. Overlapping PKs on default/shard expose fallback errors; top-level behavior remains intact |
| Construction failures | New decidable invalid declarations leave registry/manage state untouched and allow corrected-name retry; constructor and subclass removed fields, class/provider/fallback errors and top-level ineffective settings included; no permission-table queries |
| Validation timing | Nested action-key checks wait for completed registration; missing selected permission keys fail only at the reached gate; static errors have runtime guards and do not depend on migrated tables |
| URL construction safety | Actual `urlpatterns`/URLconf self-cycle, two-ViewSet cycle and missing-reference failures are bounded/actionable without DB queries; valid child-before-parent generates URLs after registration; checks/request and relevant helper walks remain safe |
| Top-level policy | Reject both explicit cascade booleans, non-None Read/Write and nonempty actions before registration. Omitted/explicit None/empty defaults work; globals add no ancestry; valid provider/fallback still govern descendant requests |
| Exact keys | Card-only accepts `card`, rejects unregistered `list`; both keys stay independent; Card actually registered as `list` is valid. Navigation fallback uses actual target policy; adding a real List does not retarget Card's entry |
| Manage | Core/Guardian nested manage need ancestry plus unchanged local gate; public settings/group membership cannot bypass; local denial after ancestor success, reached 404, both modes/all-none covered; top-level unchanged |
| Redirect | Built-in Read works without action entry; explicit pair overrides; denial precedes lookup/redirect; allowed redirect's destination can independently deny; arbitrary redirects gain no built-in exemption |
| Migration | Core-parent object-only/model-only outcomes and Guardian-parent migration; fallback independence both directions/across descendants; removed fields error; nested create/local list/object/state behavior retained |
| Helpers and diagnostics | Immediate-parent policy/nearest pair, none skips only that gate, unavailable context retains existing False behavior, invalid configuration surfaces, no new full-chain rendering checks, ancestor/local fallback displayed independently including create applicability |
| Mutation boundary | Both modes: shared-M2M edit visible through other parent, valid editable-parent FK move not automatically blocked/authorized, ordinary delete retained; document an application-owned restriction and no all-membership traversal |
| Performance and revocation | Measured one-/three-level comparisons, no top-level ancestor queries, no higher permission checks nearest-only, explained duplicate work, grants revoked before next request take effect |
| Release documentation | Breaking changelog and `docs/migrating-1.0.md` with explicit custom-key complete-pair example, built-in/top-level exceptions and check/runtime failures; provider, fallback, manage, queryset/DB, Resource, mutation and UI boundaries documented |

Reuse existing fixtures and evidence where appropriate, including
[authorization matrix](../../tests/test1/test_authorization_matrix.py),
[fragment authorization](../../tests/test1/test_fragment_authorization.py),
[Guardian policy](../../tests/test1/test_guardian_policy.py), and the parent-none, composition, content-type,
child-link, cancel, action-state, and Resource tests indexed in the historical design's technical addendum.
Snapshot/restore the process-global ViewSet registry in dynamic tests. Existing routed/superuser tests can
supply rejection and top-level preservation fixtures; they do not establish nondefault ancestor support.

## Deferred and unsupported work

The first wave does not include:

- Full ancestor parity across navigation, buttons, breadcrumbs, cancel destinations, or child tabs; only the
  specified migration of consumers of removed fields is required.
- Grant assignment/synchronization, membership repair after moves, destination-parent authorization,
  automatic form-field pinning, all-membership traversal, or generic mutation policies.
- Resource ancestors, inferred ORM relationships, a generic Resource membership-validation API, or
  nondefault/cross-database nested ORM/auth support.
- Per-view traversal flags, a public provider/operation plugin registry, dispatched ancestor endpoints,
  a replacement URL router, or persistent authorization/ancestry caches.
- Separate custom-form documentation cleanup, broader manage-page exposure redesign, or unrelated review
  findings. Required custom-declaration migration and nested-manage behavior remain in scope.
- GSD planning or implementation until separately requested.

## Decision traceability

This appendix is provenance, not a second set of cumulative rules or a task checklist. “Effective” means the
decision is represented by the final topic contract, incorporating later refinements. “Scope/process” records
a continuing boundary or historical workflow instruction rather than an implementation feature. Original
wording and approval history remain in the original ledger and discussion.

| Original ID | Disposition | Effective location and treatment |
| --- | --- | --- |
| D-01 | Scope | [Scope](#scope-and-responsibility-boundaries), [deferred work](#deferred-and-unsupported-work): ancestor authorization; other findings remain separate |
| D-02 | Effective constraint | [Handoff](#status-and-gsd-handoff), [implementation guidance](#implementation-guidance-and-discretion): developer maintainability |
| D-03 | Effective | [Scope](#scope-and-responsibility-boundaries), [request order](#request-order-and-denial-behavior): one shared explicit mechanism, no ancestor dispatch |
| D-04 | Effective | [Scope](#scope-and-responsibility-boundaries): plain and permission-required endpoints |
| D-05 | Effective | [Scope](#scope-and-responsibility-boundaries), [request order](#request-order-and-denial-behavior): independent optional child-local gate |
| D-06 | Effective | [Provider selection](#provider-and-cascade-selection): core model / Guardian object defaults; D-40 explains migration |
| D-07 | Effective | [Configuration](#public-configuration), [validation](#validation-and-safe-ancestry-construction): explicit none only, keep walking |
| D-08 | Effective | [Provider selection](#provider-and-cascade-selection): full cascade default |
| D-09 | Effective | [Provider selection](#provider-and-cascade-selection): nearest protected only when disabled |
| D-10 | Effective | [Scope](#scope-and-responsibility-boundaries), [request order](#request-order-and-denial-behavior): full relationships in both modes, including create; D-39 bounds Resource responsibility |
| D-11 | Effective | [Operations](#operation-requirements): default Read view/view |
| D-12 | Effective | [Operations](#operation-requirements): default Write change/view through none levels |
| D-13 | Effective | [Operations](#operation-requirements): create/update/delete including GET; parent change for child deletion |
| D-14 | Effective | [Configuration](#public-configuration), [operations](#operation-requirements): complete configurable pairs |
| D-15 | Effective | [Provider selection](#provider-and-cascade-selection): denial cannot select a farther alternative |
| D-16 | Effective boundary | [Configuration](#public-configuration): global/ViewSet configuration, no per-view traversal flags |
| D-17 | Effective | [Operations](#operation-requirements), [migration](#migration-and-diagnostics): explicit nested custom declarations; top-level exception |
| D-18 | Effective | [Provider selection](#provider-and-cascade-selection): optional strict-by-default Guardian ancestor fallback |
| D-19 | Scope | [Scope](#scope-and-responsibility-boundaries), [helper migration](#existing-helper-consumers): authoritative requests, full UI parity deferred |
| D-20 | Effective constraint | [Performance](#performance-and-caching): measure cost; nearest-only still resolves ancestry |
| D-21 | Effective | [Provider selection](#provider-and-cascade-selection), [migration](#migration-and-diagnostics): one mechanism, no invented child-add fallback |
| D-22 | Effective migration constraint | [Migration](#migration-and-diagnostics): direct downstream migration, no broad compatibility layer |
| D-23 | Process/history | [Handoff](#status-and-gsd-handoff): retain notes; original no-commit timing was subsequently overridden by explicit commit instructions, not a feature requirement |
| D-24 | Continuing documentation constraint | [Handoff](#status-and-gsd-handoff): confidentiality and generic examples |
| D-25 | Continuing documentation requirement | [Implementation guidance](#implementation-guidance-and-discretion), this appendix: preserve evidence and resumption context |
| D-26 | Effective | [Provider selection](#provider-and-cascade-selection): requested ViewSet overrides global in either direction; ancestor cascade does not stop descendants |
| D-27 | Documentation form | Decision tables retained in configuration, selection, operations, failures, migration and acceptance |
| D-28 | Effective | [Validation](#validation-and-safe-ancestry-construction), [migration](#migration-and-diagnostics): explicit removed parent fields fail, including subclass/default declarations |
| D-29 | Partly superseded by D-39 | [Scope](#scope-and-responsibility-boundaries): retain supported ORM metadata boundary; replace blanket Resource exclusion with Resource-leaf support |
| D-30 | Effective, refined by D-43 | [Request order](#request-order-and-denial-behavior): actor/response contract including existing early endpoint denials |
| D-31 | Effective, extended by D-46 | [Operations](#operation-requirements): finite family table, subclasses, fragments and explicit overrides |
| D-32 | Effective, refined by D-43 | [Request order](#request-order-and-denial-behavior): static → early actor → interleaved top-down lookup/gates → remaining local work |
| D-33 | Effective | [Configuration](#public-configuration): small typed configuration, no execution methods/framework |
| D-34 | Effective | [Helper migration](#existing-helper-consumers): immediate-parent consumers and manage diagnostics, no higher rendering traversal |
| D-35 | Effective | [Configuration](#public-configuration): approved classes, fields, defaults and complete pair semantics |
| D-36 | Effective, clarified by D-44/D-47/D-48/D-53 | [Validation](#validation-and-safe-ancestry-construction): strict values, failure types and stages |
| D-37 | Effective | [Configuration](#public-configuration): exact global settings and public exports |
| D-38 | Process/authorization boundary | [Handoff](#status-and-gsd-handoff): approved spec, planning deferred; no inferred phase |
| D-39 | Effective; amends D-29 | [Scope](#scope-and-responsibility-boundaries): Resource leaves under ORM ancestry, application-owned leaf scoping |
| D-40 | Effective migration requirement | [Core-parent migration](#core-parent-and-guardian-child): model versus object default and migration to Guardian parent |
| D-41 | Effective migration/diagnostic requirement | [Fallback migration](#independent-global-permission-fallback): separate ancestor and local scopes, no automatic copying |
| D-42 | Effective, refined by D-43 | [Request order](#request-order-and-denial-behavior), [integration guidance](#implementation-guidance-and-discretion): shared enforcement across MROs before remaining local processing |
| D-43 | Effective | [Request order](#request-order-and-denial-behavior): actual early actor denials before lookup even for all-none, preserve public admission |
| D-44 | Effective | [Validation](#validation-and-safe-ancestry-construction): decidable failures before registry/manage side effects; corrected-name retry |
| D-45 | Effective | [Operations](#operation-requirements), [migration](#migration-and-diagnostics): nested manage ancestry plus independent administrative gate |
| D-46 | Effective | [Operations](#operation-requirements): built-in child redirect Read; destination independently authorized |
| D-47 | Effective | [Validation](#validation-and-safe-ancestry-construction): reject ineffective top-level request declarations; allow None/empty defaults and valid provider settings |
| D-48 | Effective | [Operations](#operation-requirements): exact action keys; navigation aliases unchanged |
| D-49 | Effective release-documentation requirement | [Migration](#migration-and-diagnostics), [acceptance](#acceptance-requirements): custom declarations in Breaking/migration notes for core/Guardian, both modes |
| D-50 | Documentation correction | [Configuration example](#public-configuration): `ParentViewSet` imported from existing public module |
| D-51 | Effective | [Querysets and databases](#ancestor-querysets-identity-and-databases): scoped ViewSet resolution, actual child context, structural parent reuse, default DB only |
| D-52 | Effective boundary | [Mutation boundary](#mutation-boundary): URL path only; application owns additional effects/constraints |
| D-53 | Effective | [Validation](#validation-and-safe-ancestry-construction): safe metadata validation before URL construction and other walks; valid forward references retained |
