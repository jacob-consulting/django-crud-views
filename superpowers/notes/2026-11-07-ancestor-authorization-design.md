# Ancestor authorization for nested ViewSets

> **Historical design and approval ledger.** The effective specification is now
> [design v2](2026-11-07-ancestor-authorization-design-v2.md), which consolidates approved D-01–D-53 by topic.
> The body below is preserved as history, including superseded wording and earlier handoff instructions.
> Use v2 for future discussion/planning; its handoff replaces the instruction below to copy the whole ledger.
> Planning and implementation remain deferred until separately requested.

Date: 2026-11-07. Status: final spec approved by the maintainer, with review resolutions D-39–D-53 approved;
all Fable and Astra findings have approved dispositions. Planning explicitly deferred; not implemented.

This is a project-sized change affecting core and Guardian request authorization. Keep this document in the
notes directory. The maintainer subsequently authorized a documentation commit; the C-01/C-02 update was
committed as `db4c2cc6`. This does not authorize implementation. No identifying information from the separately
reviewed application belongs here. Discussion record: [Guardian child permissions](2026-11-07-guardian-child-permissions-discussion.md).

## GSD handoff: decisions already discussed

### Instructions to gsd-discuss-phase, researchers, and planners

This section is the authoritative decision ledger for this feature. The maintainer explicitly requested it
so a future GSD discussion does not repeat the questions already answered. Read it before identifying gray
areas. Copy the confirmed decisions into the phase's CONTEXT.md with these IDs and this document as their
source. Do not ask the maintainer to choose them again. If new code evidence creates a genuine conflict,
identify the affected decision and the evidence; ask only about that conflict.

No phase number has been assigned to this feature in this conversation. Do not attach it to the phase of the
currently checked-out branch just because this document was written there. Final spec approval is recorded in D-38, with an explicit instruction not to write a plan yet. Permission
to plan or implement must not be inferred from that approval. Do not start a GSD workflow, create
phase files, stage, or commit as a side effect of reading it.

### Confirmed decisions — preserve, do not reopen

| ID | Decision | Reason / boundary |
| --- | --- | --- |
| D-01 | First-wave subject is nested ancestor authorization from finding 23. | Custom-form documentation, manage-page exposure, and child navigation tabs are separate work. |
| D-02 | Human readability and maintainability are hard acceptance criteria. | Complex code that merely works or passes tests is unacceptable; simplify or narrow the scope. |
| D-03 | Use one shared ancestor-authorization mechanism with explicit ViewSet policies. | Do not infer protection from whichever views are registered or dispatch ancestor views. |
| D-04 | Plain views participate as well as permission-required views. | A child endpoint without local permissions must not bypass configured ancestor checks. |
| D-05 | Endpoint-local permissions remain independent. | Parent permission does not waive a child object/model permission; a plain child can deliberately have no local gate. |
| D-06 | Ancestor provider defaults are model permissions for core ViewSet and object permissions for GuardianViewSet. | These are class defaults, not inference from registered views. |
| D-07 | An intentionally unprotected ancestor explicitly declares none. | Continue through it; a missing declaration/key or failed grant must never masquerade as none. |
| D-08 | Full permission cascading is the default. | Protect newcomers against accidentally omitting ancestor authorization. |
| D-09 | Cascade disabled means check only the nearest protected ancestor. | It does not disable all ancestor authorization; pass through none levels until a protected level is found. |
| D-10 | Validate the whole declared URL relationship chain in both cascade modes. | Permission-check depth and relationship validity are different concerns. |
| D-11 | Read operations require view on protected ancestors selected by the cascade mode. | Standard child list/detail are reads. |
| D-12 | Writes require change on the nearest protected ancestor and view on higher protected ancestors when cascading. | A none level does not consume the change requirement. |
| D-13 | Standard child create/update/delete are writes, including opening their forms. | Use operation semantics, not GET versus POST. Deleting an address requires customer change, not customer delete. |
| D-14 | Allow different ancestor requirements, including change throughout the chain. | Other domains may require stricter or different rules; the address example is not universal. |
| D-15 | A failed nearest protected gate denies access. | Never try a more distant gate as an alternative after denial. |
| D-16 | Configuration scope is global and ViewSet-level only in wave one. | Per-view traversal configuration is deferred; operation-dependent requirements still vary within a ViewSet. |
| D-17 | Unknown custom actions require an explicit ViewSet ancestor-policy declaration. | Missing declaration is a configuration error, not a guessed read or unrestricted action. |
| D-18 | Guardian ancestor policy may explicitly accept global model permission as an alternative to an object grant. | This option is disabled by default and independent of endpoint-local Guardian options. |
| D-19 | First wave enforces requests; full button/link visibility consistency is deferred. | An existing visible button may lead to 403; no broad navigation integration is authorized. |
| D-20 | Cascade depth exists to address request cost. | Keep nearest-parent protection; actual savings must be measured because relationship work remains. |
| D-21 | Do not retain two ancestor-authorization execution modes merely to support cascade off. | Nearest-only uses the same mechanism as full cascade; a legacy Guardian fallback or forced child-add fallback is unnecessary. |
| D-22 | The maintainer controls downstream projects. | Favor a simple, explicit migration; do not invent broad compatibility layers on the assumption of unmanaged clients. |
| D-23 | Keep this discussion/design in notes and update it as decisions evolve; originally no staging or commits. | The later explicit commit request authorized the documentation commit recorded below; do not infer implementation authorization. |
| D-24 | Preserve confidentiality of the separately inspected application. | Use only generic entity/role descriptions; no identifying names or paths in summaries or artifacts. |
| D-25 | Preserve this ledger and a technical resumption addendum. | A new GSD/context session should resume from the decisions and evidence, not repeat discovery questions. |
| D-26 | P-01 approved: the requested ViewSet's explicit cascade value overrides the global default in both directions; unset inherits. | The global setting is a default, not a master switch. An ancestor's own setting cannot interrupt a descendant's traversal. |
| D-27 | Include and maintain decision tables for the agreed behavior. | The maintainer explicitly values them for understanding the design; keep them consistent with the ledger. |
| D-28 | P-02 approved: reject explicitly supplied removed Guardian parent-policy settings, including None/former defaults and application subclass field declarations, with actionable configuration errors. | Migrate directly to the new declarations; no silent translation, ignored policy, or legacy execution mode. Preserve independent authentication, state, and child permission checks. |
| D-29 | Original P-03 approval: nested chains must be ORM-backed, using supported FK/M2M relationship metadata; a Resource anywhere in a nested chain was excluded. **The blanket Resource exclusion is superseded by D-39.** | Historical decision retained for traceability. D-39 permits Resource leaves; Resources remain forbidden as ancestors. Unsupported ORM relationship metadata never causes a silent exemption. |
| D-30 | B-01 approved: anonymous access to protected ancestry follows the requested endpoint's existing denial policy, defaulting to login redirect. Authenticated permission denial and inactive users encountering protected ancestry receive 403. All-none ancestry adds no login requirement. | Preserve existing configured anonymous 403/404 behavior; do not consult an ancestor's endpoint response preferences or add a new per-view traversal flag. Existing local actor rules still apply; D-43 requires their early denials before ancestor lookup even for all-none ancestry. |
| D-31 | B-02 approved: use the finite built-in operation table; normal subclasses retain their family, and formset fragments use the owning editor's requirements. Explicit ViewSet action entries override the standard ancestor requirements for that key. | Generic actions/custom forms/workflow require explicit declarations. Do not infer policy from HTTP method, cv_key, or cv_permission alone. No extensible operation registry or per-view traversal flags. |
| D-32 | B-03 approved: validate static configuration, apply selected ancestry's actor policy, then resolve ancestors outermost inward and check each selected permission immediately after validating that ancestor. Stop at the first reached failure before processing deeper levels or the endpoint. | Select nearest-protected levels from configuration before ORM lookups. Missing/mismatched ancestry yields 404 when reached; denied valid permission yields 403; invalid configuration/key is an error. Local endpoint checks remain independent. D-43 refines the early actor phase to preserve existing endpoint anonymous/inactive denials even without protected ancestry. |
| D-33 | B-04 approved: use a small typed public policy class for configuration and validation only; it performs no permission checks. | Group related declarations and validate them centrally. The shared traversal owns execution. Reject the flat-field proposal and an extensible policy-execution framework; retain explicit defaults/inheritance. |
| D-34 | B-05 approved: migrate existing Guardian helpers to the new policy for their existing immediate-parent checks, without adding higher-ancestor traversal. Retain unavailable-parent behavior and surface configuration errors; update manage diagnostics. | An immediate none policy skips that local gate while existing actor/state/custom denials remain. Request enforcement is authoritative; full navigation parity stays deferred. |
| D-35 | C-01 approved: `ViewSet.ancestor_policy` uses `AncestorPolicy`, with provider, accept_global_perms, cascade, read, write, and actions; `AncestorPermissions` requires named nearest/higher keys. | Preserve the presented defaults, explicit none versus inheritance, complete-pair replacement, and configuration-only responsibility. Validation is approved separately in D-36; global declarations and exports are approved in D-37. |
| D-36 | C-02 approved: reject invalid or ineffective configuration under the validation table; require GuardianViewSet for the guardian provider. | Structural validation uses Pydantic; registry/relationship errors use Django system checks with runtime guards. Missing selected permission keys are runtime configuration errors; no startup permission-table queries. |
| D-37 | Remaining API declarations approved: global cascade/read/write settings as listed in C-03, and public exports of AncestorPolicy/AncestorPermissions from crud_views.lib.viewset. | Global configuration covers cascade and read/write defaults; provider, Guardian fallback, and custom-action declarations stay on individual ViewSets. No identified product/API decisions remain open; final spec approval and planning deferral are recorded in D-38. |
| D-38 | The maintainer gave final approval of the complete spec and explicitly instructed: do not write a plan yet. | Preserve the approved design. Do not invoke a planning workflow, create a plan, or begin implementation until subsequently instructed. |
| D-39 | Fable review finding 1 accepted: preserve Resource leaves below one or more ORM ViewSets in both cascade modes. All ancestors must be ORM-backed; Resources cannot parent an ORM ViewSet or another Resource. | Supersedes D-29's blanket nested-Resource exclusion. Shared traversal authorizes the ORM ancestors and validates their relationships; the Resource's existing application-defined loading/scoping remains responsible for leaf membership. No generic Resource membership validator is introduced. Top-level Resources remain unchanged. |
| D-40 | Fable review finding 2 accepted as a migration-documentation gap. Keep D-06 provider defaults: core ViewSet ancestors use model permissions; GuardianViewSet ancestors use object permissions by default. | Document that existing Guardian child views beneath a core parent change from object-based to model-based parent checks, potentially removing or granting access. To retain object-based ancestor protection, migrate the parent to GuardianViewSet; C-02 still rejects provider="guardian" on a core ViewSet. Child-local checks stay independent. Add acceptance coverage for the default and migration path; no automatic compatibility translation or new mixed-composition warning. |
| D-41 | Fable review finding 3 accepted as a migration and diagnostics clarification. Keep ancestor and endpoint-local global-permission fallback independent; neither setting overrides or supplies a default for the other. | The child view's cv_guardian_accept_global_perms stops affecting ancestor checks but retains its endpoint-local role where applicable. A Guardian ancestor's AncestorPolicy.accept_global_perms controls fallback whenever that ancestor is selected, across descendant endpoints, and defaults to False. Document the migration and shared scope, distinguish both settings in manage diagnostics, and test independence in both directions. |
| D-42 | Fable review finding 4 accepted as an integration-order clarification. Enforce the already-approved B-03 ordering across all supported shipped view compositions; a check placed only in CrudView.dispatch() is insufficient. | Ancestor enforcement must precede endpoint-local permission checks, child-object loading, and action-state hooks, with the early actor-phase refinement in D-43. Keep one shared authorization implementation; small, explicit integration bridges are acceptable. The precise hook remains an implementation-planning choice and must preserve local checks and supported denial responses. Require tests proving ancestor denial prevents downstream lookup, state hooks, form/fragment processing, and writes. No permission-policy change or specific as_view/setup solution is approved. |
| D-43 | Fable review finding 5 accepted: preserve existing endpoint anonymous/inactive admission denials before ancestor lookup, even when all ancestors declare provider="none". | Refines the actor phase in B-01/B-03 and D-42 to prevent a new ancestor-existence disclosure. Static configuration validation remains first. Apply protected ancestry's actor policy where selected and preserve endpoint early actor restrictions without inventing login/inactive restrictions for otherwise-public endpoints. Respect supported backend/manage behavior; PermissionRequiredMixin alone does not prove login is required. Child-object lookup, state hooks, forms/fragments, and writes remain after ancestry succeeds. |
| D-44 | Fable review finding 6 accepted: validate new policy constraints that are decidable during construction before registering the ViewSet or creating its automatic manage view. | Construction rejected by these validations must leave no registration behind; a corrected declaration can reuse the name. Checks requiring completed registration, such as action-key existence, retain their later validation stage. Prefer validation before registration over rollback machinery; exact validator arrangement remains an implementation choice. Require clean-rejection and successful-retry tests. |
| D-45 | Fable review finding 7 accepted as a manage-access clarification. Retain the built-in manage Read classification: nested manage pages participate in normal ancestor authorization and relationship validation. | Existing manage-specific access rules remain an additional independent gate; manage settings/group membership do not bypass ancestor requirements. All-none ancestry adds no ancestor login/permission gate but still validates relationships, respecting D-43 early actor denials. Document and test the nested access change. Top-level manage behavior stays unchanged; no manage exemption is introduced. |
| D-46 | Fable review finding 8 accepted: classify the shipped RedirectChildView as Read in the finite built-in operation table. | Nested redirects use normal ancestor Read requirements without needing an action entry merely for this built-in family. Preserve existing object lookup and local checks; the destination independently enforces its own ancestor and local permissions. Explicit action overrides remain available under D-31. This does not classify arbitrary redirects or custom actions. |
| D-47 | Fable review finding 9 accepted: on a ViewSet without a parent, reject non-None cascade/read/write values and nonempty actions as ineffective request-side configuration. | None/empty defaults remain valid, including when explicitly supplied. Provider and accept_global_perms retain their ancestor-side meaning and existing validation rules. Requirements for descendant requests belong on the requested descendant ViewSet. Validate before registration under D-44; global defaults do not make top-level ViewSets invalid or add ancestor checks. |
| D-48 | Fable review finding 10 accepted: validate and resolve ancestor action overrides using exact registered view keys, without navigation aliases. | With only card registered, actions["list"] is a configuration error and actions["card"] targets that endpoint. When both keys are registered, each entry applies only to its own view. A card view actually registered as list accepts that exact key. Preserve existing navigation aliases and the built-in Read default; absent-key checks still wait for completed registration under C-02/D-44. |
| D-49 | Fable review finding 11 accepted as a migration-documentation gap. Explicit ancestor action entries for nested custom endpoints are a breaking upgrade requirement for both core and Guardian applications, in both cascade modes. | Preserve D-17/B-02: missing entries produce system-check errors and runtime configuration failures. Add a migration-table row and require the eventual feature's Breaking changelog entry and docs/migrating-1.0.md update to explain affected endpoints, exact-key declarations, and failure behavior. Built-in classified endpoints retain defaults; top-level custom endpoints need no entry. This records release-documentation requirements without changing permission policy. |
| D-50 | Fable review finding 12 accepted as an example-import cleanup: import ParentViewSet alongside AncestorPermissions, AncestorPolicy, and ViewSet from crud_views.lib.viewset. | ParentViewSet is already exported there. This makes the example consistent with the public module and changes no permission behavior or import support. All twelve Fable findings now have approved dispositions; planning and implementation remain deferred. |
| D-51 | Astra F-01 accepted: resolve each ORM ancestor through its ViewSet.get_queryset(view=requested_child_view), preserve its scope, validate URL relationships, and reuse the resolved structural parent within the request. First-wave nested traversal supports only the default database for ORM ancestry, any ORM child data, and relevant authorization records. | self is the ancestor ViewSet; view is the actual requested endpoint, with unchanged request/kwargs. Ancestor view-specific queryset overrides are not invoked. Excluded ancestors yield 404 when reached; no unfiltered fallback. Parent consumers must use the same model/PK/database identity. Nondefault queryset/routing selection is a configuration error, never silently stripped or redirected; using("default") is valid. Top-level database behavior is unchanged. |
| D-52 | Astra F-02 accepted as a mutation-boundary clarification: ancestor authorization checks the declared URL ancestry. Additional authorization or constraints needed for shared-object writes, parent changes, and effects outside that path remain the endpoint/application's responsibility. | Full cascading does not enumerate other related parents or guarantee container isolation. Preserve standard save/delete semantics; deletion is not automatically unlinking, and editable parent relationships are not automatically pinned or reauthorized. Document shared M2M and editable-parent-FK examples. No generic mutation-policy engine or new automatic write restriction is introduced. |
| D-53 | Astra F-03 accepted: invalid ancestry must fail safely at or before URL construction can enter an unbounded walk. Preserve registration-order flexibility and retain system-check/request safeguards. | Cycles and missing parent references produce bounded, actionable configuration errors identifying the affected ViewSets or chain, without database queries. A child may be declared before its parent; the reference must resolve when URLs are constructed or the chain is otherwise needed. Reuse a small structural validation mechanism across relevant ancestry walks; no new routing architecture or persistent cache is required. |

The customer/address explanation is settled: addresses form part of customer configuration, so managing
addresses requires customer change under the chosen default. A deeper example is Organization → Customer →
Address (none) → Instruction: an instruction write requires customer change and, with cascade on, organization
view, plus any instruction-local permission. With cascade off, organization permission is not checked, but
the complete relationship chain must still match.

### Superseded alternatives — do not revive from earlier notes

- Total authorization opt-out: replaced by nearest-protected-only mode, D-09.
- Keeping old Guardian parent checks only when the new mechanism is disabled: replaced by one mechanism,
  D-21. The old mixin's independent authentication/state responsibilities still need preservation.
- Adding a child model-add fallback solely because cascade is disabled: unnecessary under D-09. Existing
  nested Guardian creation still relies on ancestor authorization; all-none ancestry is explicit policy.
- Requiring change on every ancestor by default: replaced by D-12; available as a stricter requirement.
- Inferring ancestor protection from registered views: explicitly rejected in favor of D-03.
- Per-view traversal flags and full navigation parity in wave one: deferred by D-16 and D-19.
- Flat ancestor configuration fields as the selected public API: replaced by the configuration-only policy
  class in B-04/D-33. Earlier proposed field names are not existing APIs to implement or deprecate.
- Rejecting every nested Resource: superseded by D-39 after review of the shipped Resource-leaf support.
  Resource ancestors remain unsupported; Resource leaves retain their existing scoping contract.

### Proposal status — distinguish approved decisions from open proposals

| ID | Boundary and status | How to handle in GSD |
| --- | --- | --- |
| P-01 | **Approved (D-26):** explicit requested-ViewSet cascade overrides the global default in either direction. | Do not ask again; use the precedence table below. |
| P-02 | **Approved (D-28):** reject explicit removed Guardian parent settings with an actionable migration error. | Do not ask again; the migration table specifies constructor values, None/default values, and subclass declarations. Validation mechanics remain implementation work. |
| P-03 | **Approved as amended (D-29/D-39):** support declared ORM FK/M2M ancestry and Resource leaves beneath it; reject unsupported ORM relationships and any Resource ancestor. | Resource leaf membership remains application-defined through the existing Resource loading/scoping contract. Do not add generic Resource relationship validation. Top-level Resources are unchanged. |

The complete design has final maintainer approval (D-38), with P-03 amended by D-39; planning is explicitly
deferred. P-01–P-03 and B-01–B-05 are approved as recorded. The concrete
configuration-class API, validation rules, global settings, and public exports are approved in C-01–C-03
(D-35–D-37). Those original product/API decisions are settled. Astra F-01–F-03 are resolved by D-51–D-53;
all Fable and Astra findings have approved dispositions. Do not repeat the settled choices.
Final spec approval does not override the explicit planning deferral or authorize implementation.

The maintainer subsequently requested discussing P-01, P-02, and P-03 one at a time and requires a design with
no open behavioral decisions because this affects the product's core. Resolve them sequentially, then audit
the sections labeled engineering discretion for any unresolved authorization or externally observable behavior.
Do not leave those decisions to an implementer's guess. Routine implementation mechanics may remain discretion
only when they do not change the agreed contract. The B-01–B-05 and C-01–C-03 reviews are complete.
The consolidated document has final approval. The maintainer explicitly deferred writing a plan.

### Engineering discretion — settle without repeating the product discussion

Use the approved configuration-only policy class and concrete API in C-01–C-03. Private helper layout, check IDs,
request-local storage, and enforcement-hook mechanics remain engineering choices. AuthTraversalMixin was an
illustration of the shared contract, not an approved public class name. No new public symbols currently exist.

The policy class declares requirements without executing them. Its schema, validation, global settings,
and exports are specified in C-01–C-03; these are not implementation discretion. Preserve B-01–B-03 when
choosing the enforcement hook. D-51 fixes the ancestor queryset source, view context, parent identity, and
default-database boundary; those are not implementation discretion either.

For a future CONTEXT.md: put the feature boundary under Domain, D-01–D-53 under Decisions with IDs, engineering
choices under the workflow's discretion section, the example above under Specifics, and per-view overrides,
full visibility parity, role/grant repair, and unrelated findings under Deferred Ideas. P-01/P-02/P-03 are
settled, as are B-01–B-05 and C-01–C-03 below. Carry only new evidence-backed conflicts forward;
do not re-ask approved choices. Do not create that phase artifact during this task.

### Behavior-closure decisions

The maintainer requires no open observable or security decisions in the final design. These details were
reviewed one at a time and approved; preserve them alongside the approved concrete public API:

| ID | Detail to settle | Why it is not merely an implementation choice |
| --- | --- | --- |
| B-01 | **Approved (D-30), refined by D-43:** preserve endpoint anonymous denial behavior, defaulting to login redirect for protected ancestry; protected authenticated/inactive denial is 403; all-none adds no login rule but retains existing early endpoint actor denials. | Existing endpoint anonymous/inactive denials precede ancestor lookup even for all-none chains; see B-03/D-43. |
| B-02 | **Approved (D-31):** finite built-in classification table and explicit ViewSet action overrides. | Do not reopen or guess additional built-in classifications. |
| B-03 | **Approved (D-32), refined by D-43:** static configuration, applicable ancestry and existing endpoint early actor checks, then top-down relationship and selected permission checks interleaved; stop at first reached failure. | Preserve early endpoint anonymous/inactive denials without adding a universal login requirement. Concrete validation representation is B-04. |
| B-04 | **Approved (D-33):** typed policy class for configuration/validation only, with no permission checks. | Preserve the class decision and the concrete schema/validation/exports approved in C-01–C-03. |
| B-05 | **Approved (D-34):** migrate existing immediate-parent helper checks and manage diagnostics without full ancestor traversal for rendering. | Preserve the approved migration table; request enforcement alone guarantees selected-ancestry authorization. |

These are approved constraints, not permission to add features. Ask the maintainer only if new evidence
exposes a behavioral conflict with the approved contract. Test isolation, routing/content-type
correctness, and integration ordering remain engineering work under the resulting explicit contract; surface
new unsupported cases instead of silently expanding the scope.

## Intent and confirmed decisions

Nested URLs must enforce the nearest protected ancestor and, by default, all higher protected ancestors,
including when the requested view or an intermediate level has no independent permission requirement.
Relationship filtering currently prevents
cross-parent object mismatches but does not supply ancestor authorization for plain core child views.
Guardian child views currently check only the immediate parent.

The motivating case is a user with access to selected customers and broad address model permissions. A valid
relationship in the URL must not expose another customer's addresses without authorization on that customer.

The maintainer confirmed:

- Cascading enabled by default, with global and ViewSet overrides. No per-view traversal settings in wave one.
- Explicit requested-ViewSet cascade values override the global default in either direction; unset inherits.
- Cascade disabled still checks the nearest protected ancestor; it skips only higher ancestor permission checks.
- Explicitly unprotected levels contribute no gate and do not stop the search for the nearest protected ancestor.
- Relationship validation covers the entire declared URL chain in both modes.
- Reads require view on protected ancestors selected by the mode. Writes require change on the nearest
  protected ancestor and, when cascading, view above it. Unprotected levels do not consume the change requirement.
- Different requirements must be configurable, including change throughout the protected ancestry.
- Endpoint-local permission checks remain independent, including plain endpoints with no local gate.
- Unknown custom actions require an explicit ViewSet declaration; missing declarations are configuration errors.
- Ancestor policies are explicit ViewSet configuration, not inferred from registered views.
- Ancestor provider defaults are model permissions for core ViewSet and strict object permissions for
  GuardianViewSet. An intentionally unprotected ancestor explicitly declares none.
- Guardian ancestor policy supports an explicit model-permission fallback, disabled by default. This option
  affects ancestor authorization only, independently of endpoint-local Guardian options.
- First-wave scope is request enforcement; full button/link visibility consistency is deferred. Existing
  buttons may lead to a destination denied by the new ancestor checks.
- Maintainability is a hard constraint. Avoid a general authorization framework or speculative extension machinery.
- Reject explicit old Guardian parent-policy declarations with migration errors; do not translate or ignore them.
- Support ORM ancestry through declared FK/M2M metadata, including Resource leaves below it; reject Resources
  as ancestors in either mode. Resource leaf membership remains the application's scoping responsibility.
- Use a typed configuration-only policy class; permission evaluation stays in the shared traversal.

## Readability and maintainability acceptance criteria

The maintainer explicitly requires human-readable, maintainable code in the spirit of the Zen of Python.
Correctness and passing security tests do not justify an implementation whose complexity the maintainer cannot
confidently explain, debug, and change. This reinforces the repository-wide maintainability rule.

- The main flow must be easy to trace: resolve configuration, determine operation requirements, apply the
  early actor rules, resolve and validate ancestry with the selected permission checks, then continue the
  remaining existing endpoint behavior.
- Prefer a small number of explicit functions with clear inputs and outputs. Do not build a generic policy
  engine, plugin registry, recursive callback system, or hidden inheritance-based policy discovery.
- Shared integration must have one identifiable enforcement entry point. Any MRO-sensitive bridge needed for
  existing views must be small, documented, and tested; do not spread authorization across incidental hooks.
  Under D-42, small explicit bridges may call the same shared authorization implementation; they must not
  duplicate policy evaluation or create separate authorization modes.
- Keep policy declaration, relationship validation, and permission evaluation distinguishable without creating
  abstractions merely to name every step. Preserve proven local permission paths.
- Any request-local reuse must be straightforward and justified by measured duplicate work. Avoid clever
  caching, hidden mutable state, and speculative optimization.
- Errors must name the ViewSet/action and the declaration that needs correction. Document supported cases
  and limitations instead of disguising unsupported cases with automatic fallback behavior.
- Implementation review must assess whether a maintainer can follow a request and explain each denial without
  navigating a web of indirection. Tests alone are not acceptance evidence for this criterion.

If meeting the current scope would require complexity that violates these criteria, simplify the design or
return with a narrower scope proposal before building it. Do not trade away required authorization checks
silently in the name of simplicity. Exact module count, helper names, and line counts are not artificial gates.

## Approaches

**Selected: explicit ViewSet policies and shared traversal.** Each ancestor describes its permission policy;
the requested ViewSet describes the operation's ancestor requirements. A shared request mechanism resolves
the chain and checks those policies. Existing endpoint permissions and Guardian queryset filtering retain
their roles. This works without ancestor detail/update endpoints and distinguishes explicit none from unknown
configuration, at the cost of declarations alongside existing view-class choices. The maintainer selected it.

**Alternative: infer policy from registered views.** This reduces configuration but requires ambiguous rules
for missing endpoints, differently protected siblings, and custom helpers. It ties ancestor protection to
available UI endpoints. It was not selected. Neither approach should execute ancestor views.

## Scope and non-goals

Include nested core and Guardian request enforcement, plain views, creates, custom actions, and formset
fragment requests through their owning view. Validate the full ancestor relationship chain, including creates
where an existing child lookup cannot supply that validation.

Do not assign child grants, synchronize memberships, repair permissions after moves, add navigation tabs,
redesign URLs/breadcrumbs/cancel destinations, or change the endpoint's local permission policy.

**D-52 mutation boundary:** ancestry authorization covers the declared URL path. Additional authorization or
constraints required by the application's domain for shared-object edits/deletes, parent changes, and effects
outside that path belong to the endpoint/application. Full cascading checks higher ancestors on that path;
it does not discover every other parent or object affected by the operation and does not guarantee isolation
between containers. Existing endpoint-local gates remain independent.

| Operation after URL ancestry and existing local checks pass | Boundary of this feature |
| --- | --- |
| Update a Genre shared by Guardian-protected Publishers A and B through A | The shared row changes for both publishers. B is outside the URL path and gains no automatic permission check; any required protection for shared edits belongs to the application |
| Update a Book through Publisher A using a form that permits changing its publisher to B | Validating the original relationship to A does not authorize B. The framework does not automatically pin that FK or add a destination-parent gate; the application must constrain or authorize moves as its domain requires |
| Delete an object shared with another parent | Preserve normal deletion semantics; nesting does not convert deletion into unlinking from the URL parent |
| Run a custom action affecting objects outside the URL ancestry | Its declared ancestor pair covers the URL path only; the action owns any additional authorization for its effects |

An application can omit the parent field from ordinary update forms, authorize an explicit move operation,
or protect shared-child editing with suitable object permissions or other domain rules. These are examples,
not new automatic restrictions. D-51's queryset scope determines what can be resolved; it does not validate
every relationship submitted in a form or every custom-action effect. Document the shared-M2M and editable-FK
examples with their actual outcomes. No all-membership traversal or generic mutation-policy engine is added.

Approved P-03 relationship boundary, amended by D-39: every ancestor must be ORM-backed, with relationships
between ORM levels expressed through existing ParentViewSet FK/M2M metadata that establishes membership
unambiguously. The requested endpoint may be an ORM model or a Resource leaf. Unsupported ORM relationships
and any Resource ancestor produce configuration errors in both cascade modes, never a bypass.

| Configuration | Approved first-wave behavior |
| --- | --- |
| ORM parent/child chain using declared FK relationships | Support full and nearest-only modes |
| ORM chain using existing declared M2M relationship metadata | Support both modes; validate actual membership on the URL path. Shared-object mutation effects remain subject to D-52's application-owned boundary |
| Relationship between ORM levels not expressible/validatable through the supported metadata | Configuration error; no guessing or silent exemption |
| Resource leaf beneath one or more ORM ViewSets | Supported in both modes; shared traversal validates and authorizes ORM ancestry, while existing Resource loading/scoping establishes leaf membership |
| Resource is a parent/ancestor of an ORM ViewSet or another Resource | Unsupported; configuration error in either mode. Resources must be leaves |
| Top-level Resource endpoint | Existing behavior unchanged; no ancestor chain to authorize |

D-39 preserves the shipped Resource-leaf configuration, superseding D-29's original blanket exclusion.
For example, Organization (ORM) → Publisher (ORM) → Files (Resource) remains supported; nothing may be nested
beneath Files. Shared traversal resolves and authorizes Organization and Publisher and validates their ORM
relationship before Resource loading. It does not need an ORM relation from Files to Publisher.

ResourceViewMixin passes URL kwargs to the Resource's existing `cv_get_items()` / `cv_get_item()` paths.
The application remains responsible for restricting the Resource collection/object to its URL parent.
The framework does not independently verify Resource leaf membership, infer a relationship, or add a generic
Resource relationship-validation API. References to full-chain relationship validation mean all declared ORM
relationships plus the endpoint's existing scoping responsibility for a Resource leaf. Ancestor enforcement
still applies to Resource leaves, including plain endpoints, with the same operation declarations, cascade
selection, and denial ordering as other endpoints. Top-level Resource behavior remains unchanged.

Confirmed UI boundary: no integration of traversal into every link/rendering helper in this wave.
Some buttons can lead to newly denied destinations; document this while guaranteeing request enforcement.
Existing helpers that read replaced Guardian policy fields need an explicit migration treatment below.

## Configuration semantics

### B-04 decision: typed policy configuration class

**Approved (D-33).** The maintainer explicitly selected a policy class for configuration only, with no permission
checks. Existing Pydantic configuration patterns provide the precedent. The class groups declarations and
validates their structure; it does not own request handling, user access evaluation, or database queries.
Shared traversal remains the single execution path.

| Representation | Strength | Cost / risk | Decision |
| --- | --- | --- | --- |
| Flat ViewSet fields and dictionaries | Few new public types | Related values scattered; repeated string keys; cross-field validation | Not selected |
| Small typed policy configuration object | Readable grouping, completion/types, centralized validation | Defaults and inheritance must be explicit | **Selected** |
| Subclass-driven execution framework | Extensive customization | Hidden execution paths and unnecessary complexity | Not selected |

Responsibility boundary:

| Responsibility | Policy configuration class | Shared traversal / integration |
| --- | --- | --- |
| Declare provider, fallback, cascade depth, and operation requirements | Yes | Consume the declarations |
| Validate configuration structure and values | Yes, without database queries | Validate registry/relationship-dependent configuration at the appropriate stage |
| Resolve defaults using the owning ViewSet and global configuration | Retain unambiguous declared/inherited values | Resolve effective configuration explicitly without changing the declaration |
| Load ancestors and validate URL relationships | No | Yes |
| Evaluate user/model/Guardian permissions | **No** | **Yes** |
| Return login/403/404 responses or dispatch a request | No | Yes, under the approved request contract |
| Store users, requests, loaded objects, or grant results | No | Request-local state only where needed |

Configuration has two distinct roles: provider/global fallback describe the owning ViewSet when it is an
ancestor; cascade/read/write/action requirements describe requests targeting it. Keep these meanings explicit
while grouping them in the configuration object.

The ancestor fallback is not a ViewSet-level default for `cv_guardian_accept_global_perms` on its views.
That view-level flag controls a separate endpoint-local gate where applicable; it neither overrides nor
inherits the ancestor fallback. D-41's migration example below makes these separate scopes explicit.

Absent/inherited values must remain distinct from explicit none or False. Constructing a policy with only
cascade specified must preserve a GuardianViewSet's object-permission default. Invalid declarations must not
be interpreted as an unprotected level. No plugin registry, implicit discovery, callback language, or policy
subclass execution mechanism is introduced.

The architectural choice, responsibilities, C-01 API shape, and C-02 validation rules are approved.
Global setting declarations and public exports are approved in C-03 (D-37). Historical flat-field snippets
are removed from this operative section so a fresh implementer cannot mistake them for the selected API.

### C-01 approved: concrete configuration-class API

**API shape approved (D-35); not implemented.** This section continues B-04 without reopening its
class-versus-flat configuration decision. The public types are `AncestorPolicy` and `AncestorPermissions`;
the approved export location is `crud_views.lib.viewset`. `ViewSet.ancestor_policy` contains an `AncestorPolicy`, with a fresh default instance
per ViewSet. These are configuration data types, with no permission-check or request methods.

`AncestorPermissions` is a small typed value with two required, named string fields: `nearest` and `higher`.
Both are permission-map keys such as `view` or `change`, resolved separately against each selected ancestor's
permission map. Named fields avoid positional tuples and repeated unvalidated dictionary structures.

| `AncestorPolicy` field | Declared default | Meaning |
| --- | --- | --- |
| `provider` | `None` | Use owning ViewSet class default: model for core, guardian for GuardianViewSet. Explicit choices: `"model"`, `"guardian"`, `"none"`. |
| `accept_global_perms` | `False` | When this ViewSet is a Guardian-protected ancestor, permit model permission as an alternative to its object permission. |
| `cascade` | `None` | For requests targeting this ViewSet, inherit the global cascade default; explicit True/False overrides it. False still checks the nearest protected ancestor. |
| `read` | `None` | Inherit global read requirements; otherwise supply a complete `AncestorPermissions` pair. |
| `write` | `None` | Inherit global write requirements; otherwise supply a complete `AncestorPermissions` pair. |
| `actions` | Fresh empty dictionary | Map exact registered view keys to complete `AncestorPermissions` pairs; no navigation aliases (D-48). An entry overrides the read/write requirement for that operation. Nested custom operations require an entry; D-47 rejects nonempty actions on a ViewSet without a parent. |

`provider=None` means the owning class default, never unprotected. Only the string `"none"` intentionally
removes that ancestor's gate. Setting only `cascade=False` on a GuardianViewSet therefore preserves its
Guardian provider. `read=None` and `write=None` mean inheritance, never a permission exemption. A declared
pair replaces that operation's whole inherited pair; there is no merging of individual nearest/higher fields.
Ancestor ViewSets' read/write/action settings are not inherited by descendants.

Approved global declarations in Django settings (C-03/D-37), shown with package defaults:

```python
CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE = True
CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS = {"nearest": "view", "higher": "view"}
CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS = {"nearest": "change", "higher": "view"}
```

The two global mappings are validated as complete `AncestorPermissions` values. Django settings need no
imports from the ViewSet module. Global configuration covers cascade and read/write defaults; provider,
Guardian fallback, and action-key declarations remain explicit on individual ViewSets. No global action-key
map guesses the meaning of identically named custom endpoints in different ViewSets.

The following illustrate the approved API shape; these are not executable current-package APIs. Application model imports
are omitted. The first example declares provider policy only; local endpoint permissions remain determined
by the registered view classes.

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

With package defaults, a write request to an address checks customer change. Address's provider none does
not disable its own request traversal. If a deeper child is added, Address contributes no ancestor gate;
Customer becomes the nearest protected ancestor. Actual FK names must match `ParentViewSet` metadata.

Examples of alternative policy declarations (each is independent):

```python
# Nearest protected ancestor only; the owning ViewSet's provider stays at its class default.
AncestorPolicy(cascade=False)

# Require change throughout the selected protected ancestry for write operations.
AncestorPolicy(
    write=AncestorPermissions(nearest="change", higher="change"),
)

# Explicit ancestor requirements for a registered custom view with cv_key="approve".
AncestorPolicy(
    actions={
        "approve": AncestorPermissions(nearest="change", higher="view"),
    },
)

# On a GuardianViewSet: accept global grants when it is checked as an ancestor.
AncestorPolicy(accept_global_perms=True)
```

### C-02 approved: validation rules

**Approved (D-36), construction ordering clarified by D-44 and top-level configuration by D-47.**
The maintainer approved the validation rules and requested retaining the table in the spec. It includes
settled resolution behavior for context. Structural validation also applies to the global values approved in C-03.
D-48 clarifies exact registered action keys and excludes navigation aliases from policy resolution.
D-53 requires ancestry validation to be safe at URL construction as well as in check/request paths.

| Situation | Required API behavior |
| --- | --- |
| Policy omitted, or an empty `AncestorPolicy()` | Class provider default, strict Guardian fallback, inherited cascade/read/write, no custom action declarations |
| Exact action-key entry exists on a nested ViewSet | Use its entire pair; otherwise use the built-in family's effective read/write pair; unknown nested custom operation without an entry is an error |
| ViewSet has no parent and its policy has non-None cascade/read/write or nonempty actions | Construction-time configuration error identifying the ineffective fields; reject before registration under D-44 (D-47) |
| ViewSet has no parent and its policy has cascade/read/write=None and actions={} | Valid, whether omitted or explicitly supplied; provider and accept_global_perms remain subject to their existing rules. Global request defaults do not invalidate this configuration (D-47) |
| Global read/write setting omitted | Package pair applies; explicitly supplied global mappings must contain both fields |
| Unknown policy/pair field, invalid provider, cascade other than a boolean or None, non-boolean fallback, empty or whitespace-padded permission key, incomplete pair | Validation error; reject rather than coerce, ignore, or partially merge |
| `None` where a pair field or action pair is required | Validation error; no permission-skipping sentinel in permission pairs |
| `provider="guardian"` on a core ViewSet | Configuration error directing the developer to GuardianViewSet, which supplies Guardian's permission-map/content-type semantics |
| `provider="model"` or `"none"` on a GuardianViewSet | Explicit ancestor provider choice; local Guardian views retain their own behavior |
| `accept_global_perms=True` with effective provider other than guardian | Configuration error; the flag would have no effect |
| Action key not literally registered on its owning ViewSet, even if navigation lookup resolves it through an alias | Configuration error once view registration is complete; no premature rejection while ViewSet is being constructed. Policy validation/resolution uses exact keys; navigation aliases remain unchanged (D-48) |
| Required permission key absent from a selected ancestor's permission map | Runtime configuration error under B-03; no startup permission-table query |
| A nested request selects a nondefault database for ORM ancestry, any ORM child data, or relevant authorization records | Unsupported in wave one; configuration error when that selection is reached. Do not discard using(...) or override routing to force default. Explicit using("default") is valid; top-level behavior is unchanged (D-51) |
| A cycle or missing parent reference is reached during URL construction or another supported ancestry walk | Bounded, actionable configuration failure before an unbounded walk; identify the affected ViewSets or chain. Keep Django system-check errors and ImproperlyConfigured guards for URL construction/request paths; no database queries (D-53) |
| A child is declared before a valid parent ViewSet is registered | Allow the forward reference during construction; it must resolve when URLs are constructed or ancestry is otherwise needed. Do not reject solely because registration is still incomplete (D-53) |
| New policy constraint decidable during ViewSet construction is invalid | Reject before registry insertion and automatic manage-view creation; leave no registration behind, so a corrected declaration can reuse the same name (D-44) |

Structural validation uses the existing Pydantic validation style (`ValidationError` at construction).
Cross-ViewSet, completed-registry, and relationship failures are Django system-check errors with a runtime
`ImproperlyConfigured` guard. Runtime permission-key configuration failures use `ImproperlyConfigured`.
Messages must identify the ViewSet, action where relevant, and offending declaration/key; they must not
include request/user/grant state. Configuration is resolved without mutating the declared objects. Each
policy owns its action dictionary; request-specific data is never stored in either type.

D-44 requires new construction-time policy validation to precede registration side effects. This includes
owning-class checks such as guardian provider on a core ViewSet, fallback with an effective non-guardian
provider, explicit removed parent-policy declarations, and D-47's ineffective request settings when there is
no parent. These cannot all be validated by AncestorPolicy alone, because some require the owning ViewSet's
class or parent declaration, but they do not need completed view registration or permission-table queries.
A failed declaration must not leave its name in `_REGISTRY` or an automatically
registered manage view behind. A valid corrected declaration using that name must then construct normally.

Prefer checking before registration rather than adding rollback machinery; private validator arrangement
remains an implementation choice. Existing `register()` is a side-effecting after-validator, so adding another
after-validator later in the sequence is not sufficient. Completed-registry checks, including action-key
existence, remain deferred until registration is complete; D-47's rejection of any nonempty actions on a
top-level ViewSet does not inspect whether those keys exist. Cross-ViewSet/forward-reference validation remains
deferred until resolution is needed, including safe URL construction under D-53. Runtime permission-key
resolution retains its existing stage and error contract.

D-53 closes the gap between validation and URL generation. A URLconf can access ViewSet.urlpatterns while
being imported, before a later system check or any request guard runs. Validate the required ancestry at or
before that URL-building walk so self-cycles, longer cycles, and unresolved references fail clearly instead
of hanging. Other supported ancestry walks must also terminate safely. Preserve both the system-check and
request safeguards; adding only one late check is insufficient.

Use registration metadata without model, permission, or other database queries. Error messages should identify
the affected ViewSets or chain. A valid child-before-parent declaration remains supported once registration
is complete; requesting URLs while its parent is still unresolved produces an actionable configuration error.
Prefer a small shared structural validation/walk, with the precise helper arrangement left to implementation.
No graph library, second URL-routing system, or persistent ancestry cache is required.

D-47 distinguishes the two scopes of the policy. For Publisher → Book, a `write` pair on Publisher would
describe requests to Publisher, which has no ancestors; it would not change requests to Book. Reject it with
an error explaining that ancestor requirements for Book requests belong on Book. The same applies to both
explicit cascade values (True and False), read pairs, and nonempty action mappings, even if the supplied values
match global defaults. This is an owning-ViewSet constraint, not a prohibition on constructing a standalone
policy value for later use with a nested ViewSet.

Keep cascade/read/write=None and actions={} valid, including explicit defaults. Provider and Guardian fallback
remain meaningful on a top-level ViewSet when it is checked as an ancestor of descendants, under the existing
class/provider validation rules. Global cascade/read/write defaults remain valid and do not create an ancestor
chain for top-level requests. Top-level custom actions require no ancestor action entry. No warning-only or
silent-ignore alternative is adopted for ineffective non-default request declarations.

D-48 uses literal registration for both action-key validation and override lookup. Navigation helpers may
resolve `"list"` to `"card"` when no list view exists, but that does not register a list view or create a second
policy key for the card endpoint. A request reaching the card endpoint through a navigation alias uses that
endpoint's actual registered key for its override, or its normal Read requirements if no entry exists.

| Views registered on a nested ViewSet | Ancestor action override behavior |
| --- | --- |
| Only `"card"` | `actions["card"]` targets the card endpoint; `actions["list"]` is a configuration error |
| Both `"list"` and `"card"` | Each key configures only its own registered endpoint; neither entry supplies the other's override |
| CardListView explicitly registered with `cv_key="list"` | `actions["list"]` is valid because it is the actual registered key; the view retains its built-in Read family |
| No override for a built-in list/card endpoint | Use its effective Read pair; an action entry is optional for these built-in families |

Preserve existing navigation fallback behavior. Supporting aliases in permission declarations would allow an
override's target to change when a real list view is later registered; exact keys keep the target explicit.
Absent-key validation still waits for completed registration, with the existing system-check/runtime-guard
contract. D-47's separate prohibition on nonempty actions for a ViewSet without a parent remains in force.

### C-03 approved: global declarations and public exports

**Approved (D-37).** The maintainer approved the remaining API declarations after the open-decision audit.

| Public declaration | Approved value / contract |
| --- | --- |
| `CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE` | Default True; explicit ViewSet cascade overrides it in either direction |
| `CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS` | Default complete pair: nearest view, higher view |
| `CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS` | Default complete pair: nearest change, higher view |
| Public import location | Export `AncestorPolicy` and `AncestorPermissions` from `crud_views.lib.viewset` |
| Global scope | Cascade and read/write defaults only; provider, Guardian fallback, and custom-action declarations stay on individual ViewSets |

The global mappings and usage examples above remain the canonical declarations. These API choices are
settled under D-35–D-38; later review resolutions amend the operative contract as recorded in the ledger.
All Fable and Astra findings now have approved dispositions. Planning is explicitly deferred; do not start
implementation. Private module layout remains an engineering choice behind the approved exports.

### Requested endpoint cascade depth

The requested ViewSet's explicit cascade-enabled/disabled value overrides the global default; unset means
inherit. Global defaults to cascade enabled. An explicit ViewSet value overrides the global default in either
direction. This is one authorization mechanism with two depths, not an on/off switch for all ancestor checks.

Approved P-01 precedence table (On means full cascade; Off means nearest protected ancestor only):

| Global cascade | Requested ViewSet setting | Effective behavior |
| --- | --- | --- |
| On | Inherit | Check all protected ancestors |
| On | Off | Check nearest protected ancestor only |
| Off | Inherit | Check nearest protected ancestor only |
| Off | On | Check all protected ancestors |
| On | On | Check all protected ancestors |
| Off | Off | Check nearest protected ancestor only |

With cascade enabled, check all protected ancestors under the configured requirements. With cascade disabled,
find the nearest protected ancestor (passing through explicitly unprotected levels), check it, and skip higher
ancestor permission evaluation. A denial at the nearest gate denies; it must never cause another gate to be
tried instead. If the entire ancestry explicitly declares none, there is no ancestor permission gate to apply.

An ancestor's cascade setting affects requests to that ViewSet, not its contribution to a descendant's checks.
Cascade depth and an ancestor's none policy are separate concepts. Full relationship validation and existing
endpoint-local checks apply in both modes. There is no legacy Guardian fallback or separate global kill switch.

| Responsibility | Cascade on | Cascade off |
| --- | --- | --- |
| Validate the full URL relationship chain | Required | Required |
| Pass through explicitly unprotected levels to find the nearest protected ancestor | Required | Required |
| Check nearest protected ancestor | Required if one exists | Required if one exists |
| Check higher protected ancestors | Required | Not performed |
| Deny when a selected ancestor gate fails | Required | Required |
| Keep endpoint-local permission checks | Required | Required |
| No protected ancestor exists because every ancestor explicitly declares none | No ancestor permission gate exists; retain relationship and local checks | Same |

Cascade off does not promise zero ancestor queries: full relationship validation remains required.

### Ancestor permission provider

Support model permissions, Guardian object permissions, and explicitly none. The small shared contract receives
the user, resolved ancestor, and required permission key. No public arbitrary backend registry in this wave.
Guardian integration lives in its extension package; core must not require Guardian installation.

Confirmed defaults: core ViewSet declares model permission behavior; GuardianViewSet declares strict Guardian
object permission behavior. An intentionally unprotected ancestor must explicitly declare none, even if its
own views are plain. These defaults come from the ViewSet class, not registered endpoints.

| Ancestor configuration | Permission evaluated at this level | Effect on upward selection |
| --- | --- | --- |
| Core ViewSet default | Required model permission | Counts as a protected ancestor |
| GuardianViewSet default | Required permission on the resolved object | Counts as a protected ancestor |
| Explicit none provider | No local permission requirement | Skip this level's permission check; do not consume the nearest-protected position |
| Invalid provider or missing required permission key | Configuration error | Do not reinterpret as none or try a weaker permission |

Provider policy describes use as an ancestor; it does not convert plain endpoint views into permission-required
views. Different local endpoint permissions are not automatically a contradiction. Explain these roles clearly.

Resolve keys through the ancestor ViewSet's permission map. Model checks evaluate model-level permissions;
Guardian evaluates the actual object using the configured content-type semantics. Its confirmed default
is strict object permission. The maintainer also confirmed an explicit provider option for global
model-permission fallback, disabled by default. When enabled, a grant of the required model permission or
the required permission on the resolved object satisfies the ancestor gate. Do not
derive this from a registered view or relax the child's own Guardian gate.

Guardian ancestor fallback decision table, for an ordinary active authenticated user and the required
permission on the correct object (superuser/backend semantics and separate gates still apply):

| Object grant, directly or through a group | Model-wide grant | Fallback off (default) | Fallback on |
| --- | --- | --- | --- |
| No | No | Deny | Deny |
| Yes | No | Satisfy this ancestor gate | Satisfy this ancestor gate |
| No | Yes | Deny | Satisfy this ancestor gate |
| Yes | Yes | Satisfy this ancestor gate | Satisfy this ancestor gate |

Invalid/missing policies or permission keys are configuration failures, never none. Protected providers deny
inactive authenticated users and preserve their backend's normal superuser semantics. None performs no local
user-permission check. Never determine whether an ancestor is protected from the current user's grants.

### Operation requirements

An operation requirement consists of the nearest protected ancestor's permission and the higher protected
ancestors' permission:

| Operation | Nearest protected ancestor, either mode | Higher protected ancestors, cascade on only |
| --- | --- | --- |
| Read default | view | view |
| Write default | change | view |
| Stricter write policy | change | change |

Standard child operation mapping:

| Requested child operation | Ancestor operation category | Required permission on nearest protected ancestor by default |
| --- | --- | --- |
| List / detail | Read | view |
| Create, including opening the form | Write | change |
| Update, including opening the form | Write | change |
| Delete, including opening confirmation | Write | change |
| Unrecognized custom action with explicit ViewSet policy | As explicitly declared | As explicitly declared |
| Unrecognized custom action without that declaration | Configuration error | No inferred fallback |

These permissions do not replace the requested endpoint's own permission requirement.

Allow the earlier discussed view/view write policy too. Values are explicit permission keys, not HTTP methods
or a callback language. Provider none decides which levels are skipped; absent keys must not silently skip.

Global mappings supply defaults; a ViewSet can override them. Custom action declarations live on the requested
ViewSet, keyed by the registered action/view key, and explicitly supply the ancestor requirement pair.

Recognize shipped list/card/detail operation families as reads and create/update/delete families as writes.
An update form GET requires write ancestry. Classification must not rely solely on arbitrary cv_key or
cv_permission values: a custom action cannot evade declaration by naming itself detail. A renamed standard
CRUD view can retain its family. Generic ActionView, custom form views, workflow transitions, and unknown
operations require explicit declarations. The builder can choose the finite classification implementation.

Built-in manage views count as read for ancestry while retaining their separate administrative gate. D-45
clarifies that this changes total access to nested manage pages: the existing local gate is preserved, and
normal ancestor checks are additional requirements. The
remaining finite classification is approved in B-02 below; it is not left to an implementer's silent choice.
Unknown-action checks apply to nested endpoints in both modes, not top-level actions with no ancestors.
Top-level ViewSets instead reject ineffective explicit request settings under D-47; their custom actions
need no ancestor declaration.

B-02 exact operation classification — **approved (D-31), extended by D-46**:

| Endpoint family | Required ancestor operation |
| --- | --- |
| Core list/card/detail, rich object detail, polymorphic detail | Read |
| Core create/update/delete and their polymorphic variants | Write, including form/confirmation GET |
| Polymorphic create-type selection | Write; it is the entry into the creation flow |
| Built-in ordered up/down actions | Write; these known actions change ordering |
| Built-in RedirectChildView | Read; loading the current object and redirecting does not grant access to the destination, which enforces its own requirements (D-46) |
| Built-in manage views | Read for ancestry; nested requests must also pass normal relationship/ancestor checks. Keep the existing independent manage gate; it does not bypass ancestry. Top-level behavior is unchanged (D-45) |
| Generic ActionView, object/no-object custom forms, workflow, other custom endpoints | Explicit ViewSet action declaration required |
| Formset fragment request | Same operation/requirements as its owning editor endpoint; GET does not imply read |

Use a small explicit classification of shipped families, including their normal subclasses and permission
variants. Renaming a standard CRUD view's cv_key retains its family. A generic action that merely uses the
name detail or permission view remains generic. A custom override that changes the semantics of a standard
family must supply an explicit declaration; the framework does not attempt to infer arbitrary method bodies.

An explicit ViewSet action entry takes precedence over the standard family requirements for that registered
key, allowing deliberate domain-specific requirements without per-view class traversal flags. It must declare
the required ancestor permissions and cannot disable traversal or reinterpret an invalid key as none. Exact
public syntax is B-04. The low-level class-recognition mechanics remain an engineering choice within this
approved behavior table; no extensible operation registry is required.
Under D-48, select an override using the requested endpoint's exact registered key, regardless of any
navigation alias used to reach it. Do not apply a different endpoint's entry through alias resolution.

Under D-46, a nested `RedirectChildView` participates in normal ancestor Read authorization and relationship
validation before its existing object lookup and redirect processing. It needs no explicit action entry merely
because it is a redirect. Preserve any independent local checks. The destination request independently applies
its own operation classification, ancestor requirements, and local permissions; a successful redirect grants
no access to that destination. An explicit action entry for the redirect's registered key can override its
ancestor requirements under the existing rules. This finite classification covers the shipped family and
normal subclasses, not arbitrary redirects or custom actions with different semantics.

### D-45 clarification: nested manage access

The existing manage-specific settings/group rules determine the local manage gate. Preserving that gate
does not preserve every formerly successful nested manage request: the new ancestor requirements apply in
addition, using the normal effective Read/action requirements and cascade mode. There is no manage exemption.
This applies to both core ManageView and GuardianManageView.

| Nested manage request | Required behavior |
| --- | --- |
| Local manage settings permit public access, but selected ancestry is protected | Apply B-01's anonymous/inactive policy and selected ancestor permission checks; the permissive manage setting is not a bypass |
| User passes the manage gate but fails a selected ancestor permission gate | Deny at the ancestor gate |
| Ancestor checks pass but the manage gate denies | Preserve the manage gate's denial |
| An admitted request reaches a missing or mismatched ancestor | 404 under B-03; manage settings/group membership do not waive relationship validation |
| All ancestors explicitly use provider none | Add no ancestor login/permission gate, preserve D-43's existing early actor checks, validate relationships, and retain the local manage gate |
| Valid ancestry, selected ancestor checks pass, and local manage gate passes | Access is permitted by these gates |

Top-level manage endpoints have no ancestry to validate or authorize and retain their existing behavior.
Document the nested access change in the manage/settings guidance and the feature's Breaking/migration notes
during implementation. This clarification does not redesign manage-specific settings, group admission,
diagnostic contents, or the separately deferred manage-exposure work.

### Worked decision tables

For Organization → Customer → Address (none) → Instruction, with Organization and Customer protected and
the standard requirement mapping:

| Level | Instruction read, cascade on | Instruction write, cascade on | Instruction read, cascade off | Instruction write, cascade off |
| --- | --- | --- | --- | --- |
| Organization | view | view | No permission check | No permission check |
| Customer | view | change | view | change |
| Address (none) | No local permission gate | No local permission gate | No local permission gate | No local permission gate |
| Instruction endpoint | Its own configured checks | Its own configured checks | Its own configured checks | Its own configured checks |

All four columns still require the complete URL relationship chain to match. A configured change/change write
policy replaces organization view with change in the cascade-on write column; cascade off still omits the
organization permission check.

Independent permission-gate outcomes:

| Selected ancestor gates | Endpoint-local permission gate | Permission result |
| --- | --- | --- |
| Any denies | Passes or absent | Denied; child permission does not override ancestor denial |
| All pass | Denies | Denied; ancestor permission does not override child denial |
| All pass | Passes or deliberately absent | These permission gates are satisfied |
| All ancestors explicitly have none | Denies | Denied by the endpoint-local gate |
| All ancestors explicitly have none | Passes or deliberately absent | No ancestor permission requirement is added; local permission result remains |

Satisfying permission gates is not a promise of a successful response: existence, relationship validity,
authentication where separately required, action state, and form validation remain independent.

## Request behavior

Before a request can be routed, URL construction must satisfy D-53's safe structural validation contract.
The request-side checks below remain necessary; they are not the only protection against invalid ancestry.

1. Resolve the requested endpoint's cascade depth. Top-level endpoints perform no ancestor loading or permission queries.
2. Validate operation/policy declarations and ancestry structure. Detect cycles, missing references, and
   unsupported relationships. Select the nearest protected ancestor and all gates required by the configured
   mode before ORM lookups, independently of user grants. Static checks must not query permission tables at
   import or prevent migrations.
3. Before ancestor object lookups, apply B-01's anonymous/inactive policy if protected ancestry is selected,
   and preserve the endpoint's existing early anonymous/inactive admission denials even for all-none ancestry
   (D-43). Do not introduce actor restrictions that the endpoint does not otherwise have when ancestry is all-none.
4. Resolve ancestors outermost first through each ancestor ViewSet's get_queryset(view=requested_child_view),
   under D-51, using declared URL argument names and relationships. Every intermediate
   relationship must match, including at none-policy levels and for create requests. Stop before entering a
   deeper scope when a permission check selected by the current mode denies. Relationship validation must not
   accidentally perform higher permission checks in nearest-only mode.
5. Interleaved with step 4, evaluate each selected permission gate immediately after that ancestor is resolved
   and its relationship validated, before resolving the next level. A denial never moves the nearest-protected
   selection upward. In cascade-off mode, the only selected gate is the nearest protected ancestor.
6. Continue the remaining existing endpoint-local checks, child queryset/object lookup, action-state handling,
   and form work.
   Do not run ancestor views or their action-state hooks.
   D-52 bounds the ancestor result to the URL path; it does not authorize destination parents or effects
   outside that path, nor add automatic restrictions to otherwise-valid form saves or custom actions.

For a Resource leaf, steps 4–5 resolve only its ORM ancestors and validate relationships between those
ancestors. Step 6 retains Resource loading/scoping through the existing URL kwargs contract; the leaf is not
subject to an ORM relationship lookup. Resource loaders must not run before selected ancestor gates pass.

**D-51 ancestor loading, identity, and database contract:**

The ancestor ViewSet's queryset is authoritative for ancestor visibility. Call its existing
`get_queryset(view=requested_child_view)` and resolve that ancestor's declared URL PK within the returned
queryset. Preserve its filters and validate every declared relationship; a custom queryset does not waive
relationship validation. A row excluded by a soft-delete, tenant, or other queryset filter yields 404 when that
lookup is reached, even if the actor holds a grant for the row. Never retry through an unfiltered manager.
These rules also apply to none-policy levels and in nearest-only mode, because lookup/relationship validation
and permission selection are separate requirements. Preserve B-03/D-43 ordering: do not call a deeper
ancestor's queryset after an earlier denial or call ancestor querysets before applicable early actor denials.

| Lookup input or consumer | Required behavior |
| --- | --- |
| self inside get_queryset | The ancestor ViewSet being resolved |
| view argument | The actual requested child endpoint; request and URL kwargs are unchanged. Its model/cv_key and any leaf pk still describe the child, not a synthesized ancestor view |
| Ancestor list/detail view-specific queryset overrides or permission mixins | Not invoked or inherited by selecting an ancestor endpoint; ViewSet queryset scope and explicit ancestor permission policy apply independently |
| Immediate structural parent used by create attachment, parent-based state checks, and supported request helpers | Reuse the resolved parent; model, PK, and database identity must agree with traversal. A none-policy structural parent remains the structural parent, even when the nearest protected ancestor is farther away |
| Custom parent-loading override that substitutes another object or database | Outside the supported contract; do not claim compatibility with a second independent parent-resolution path |

Do not manufacture or dispatch an ancestor view and do not add a new public loader API. Queryset overrides
that depend on the view argument must account for the actual requested endpoint. Existing querysets that use
view.request.user receive the current actor; existing ancestor kwargs remain available. Migrate shipped
cv_get_parent_object consumers to reuse the traversal result within that request. No persistent object or
authorization cache is introduced. Filters from the manager used by the returned queryset remain in effect;
the contract does not replace an application ViewSet queryset with model._default_manager.

Wave one supports the default database only for ORM ancestors, any ORM child data, and relevant authorization
records. A queryset or route selecting another alias is a configuration error when reached under normal
request ordering. Preserve the selection long enough to validate it: do not strip using(...), replace it with
using("default"), or silently reroute to a different copy of the row. Explicit using("default") remains valid.
Cross-database ancestry, nondefault traversal, and central-auth/sharded-data arrangements are unsupported in
this wave; no database-routing API or cross-database identity framework is added. Existing top-level database
behavior is outside this change. Resource leaves retain D-39's application-owned loading contract; their ORM
ancestry and relevant authorization records follow D-51.

The builder chooses the common entry point after inspecting MRO and Django's lifecycle. Under D-42, refined
by D-43, it must preserve the early actor phase and enforce B-03 before the remaining endpoint-local permission
checks, child-object loading, action-state hooks, form/fragment processing, or endpoint side effects in every
supported shipped composition. Existing local checks and supported denial responses must remain intact.
A check placed only in `CrudView.dispatch()` is insufficient: shipped permission-required compositions execute
Django's permission dispatch earlier, and that path can already load the child and evaluate its state.

Keep one shared authorization implementation. Small explicit integration bridges are acceptable where needed;
the exact hook is an implementation-planning choice, not a new public policy or an approved `as_view()`/`setup()`
solution. Custom overrides that bypass the documented cooperative entry point are unsupported. Checks can
identify known bad compositions but must not claim to verify arbitrary custom dispatch code.

Missing ancestors and mismatched relationships return 404 when reached. Denied authenticated users receive
403 at the reached selected gate. The B-03 ordering determines which failure is reached first: a denial at an
outer selected gate stops processing before probing deeper missing/mismatched objects.
Anonymous users use the endpoint's supported login/denial behavior; plain views need a defined path without
assuming AccessMixin. All-none ancestry preserves anonymous access unless an existing local gate denies it.

B-01 response policy — **approved (D-30), actor ordering refined by D-43**:

| Actor / situation | Required response rule |
| --- | --- |
| Anonymous request with at least one protected ancestor | Use the requested endpoint's existing supported anonymous/no-permission response policy; default to a login redirect when no such policy is configured |
| Anonymous Guardian endpoint configured for 403 or 404 | Preserve that configured response; do not replace it with a redirect |
| Authenticated active user denied a required ancestor permission | 403; do not redirect to login |
| Authenticated inactive user encounters protected ancestry | 403, regardless of grants |
| Every ancestor explicitly has provider none; endpoint's existing early actor rules deny this anonymous/inactive user | Return the existing supported login/403/404 denial before ancestor lookup, independent of whether URL ancestors exist or match |
| Every ancestor explicitly has provider none; endpoint permits this actor | Add no authentication/inactive-user restriction; continue relationship validation and remaining local checks |

This policy introduces no new per-view traversal setting. Existing endpoint denial configuration remains
endpoint behavior; an ancestor's own UI denial preferences are not consulted. Plain views without AccessMixin
need the standard login-redirect behavior supplied by the shared mechanism. Runtime ordering relative to
configuration and relationship errors follows B-03 as refined by D-43. The shared mechanism supplies the
default login redirect for plain views when protected ancestry requires it, not for all-none ancestry.

D-43 preserves actual supported admission behavior, not a guessed authentication requirement based solely on
inheritance from `PermissionRequiredMixin`. Core permission backends can permit anonymous actors, and manage
settings can permit public access. All-none ancestry must preserve that admission; Guardian's existing explicit
anonymous/inactive restrictions must also remain effective. The early phase must not invoke child lookup or
action-state hooks merely to discover an actor decision. Calling a complete local `has_permission()` pipeline
that loads an object would violate this boundary. The exact integration remains an engineering choice within
the supported behavior, without a new per-view traversal flag or a generic policy framework.

B-03 failure ordering — **approved (D-32), actor phase refined by D-43**:

| Order | Work | Failure behavior |
| --- | --- | --- |
| 1 | Validate static ViewSet/operation/relationship declarations and select the protected levels from configuration | Configuration error for missing/invalid declarations, cycles, or unsupported structure; no permission-table queries for static checks |
| 2 | Apply the protected ancestry's anonymous/inactive policy where selected and preserve existing endpoint early anonymous/inactive admission checks even for all-none ancestry | Preserve applicable B-01/endpoint denial before ancestor object lookup; add no actor restriction to otherwise-public all-none endpoints |
| 3 | Resolve the ancestor chain from outermost to immediate structural parent, checking each relationship as it is reached | Missing object or broken relationship returns 404 at that point |
| 4, interleaved with 3 | For each selected protected level, resolve the required permission key and evaluate its gate before loading deeper levels | Missing required key is a configuration error; valid key without permission returns 403; stop immediately |
| 5 | Continue the requested endpoint's remaining existing local permission/state/object checks | Preserve their existing denial behavior; ancestor success or early actor admission does not waive them |
| 6 | Run the normal endpoint handler, render forms/fragments, or process writes | Only after all required prior gates pass |

In cascade-on mode, a denied outer ancestor stops processing before a nonexistent or mismatched deeper object
is examined. In nearest-only mode, higher permissions are never evaluated, but ancestor existence and all
relationships are still validated. Selecting the nearest protected ancestor uses declarations, not database
grants, so an unauthorized level is never skipped. Top-level endpoints keep their existing request path.

| Example, with valid static configuration | Required result |
| --- | --- |
| Anonymous user, protected ancestry, arbitrary nonexistent parent PK | B-01 login/denial response before loading that parent |
| All-none ancestry; endpoint's existing early rules deny anonymous access; URL parent exists, is missing, or mismatches a higher parent | Same configured login/403/404 denial in each case; no ancestor object lookup |
| All-none ancestry; endpoint's existing early rules deny inactive users; URL ancestry is valid or invalid | Existing inactive-actor denial before ancestor lookup in either case |
| All-none ancestry; endpoint permits anonymous access, including supported backend/manage configuration | No new login requirement; reached missing/mismatched ancestry still returns 404 |
| Cascade on: outer ancestor exists but permission is denied; a deeper URL object is also missing | 403 at the denied outer gate; do not inspect the deeper object |
| Earlier selected gates pass; the next ancestor does not exist or does not belong to its URL parent | 404 |
| Cascade off: a higher ancestor exists without a user grant, all relationships match, nearest protected gate passes | No denial from the higher ancestor; continue endpoint-local checks |
| Any mode: the selected gate references a nonexistent permission key | Configuration error, never permission success or a weaker fallback |

Static validation must also have runtime protection so skipping a management check does not permit processing
an invalid action. Resolve database-backed permission vocabulary only when needed for a selected gate. A DB
failure is an error, never a reason to grant access. Concrete exception classes, actionable message contents,
and invalid-value validation belong in the public configuration contract B-04. Existing endpoint checks may
still distinguish their own missing-object/permission cases; this contract specifies ordering of the new
ancestor mechanism, not a rewrite of all local view behavior.

Top-down walkthrough for a requested Instruction under Organization → Customer → Address (none), with valid
configuration and an active authenticated user:

| Step | Relationship/existence work | Cascade-on permission work | Cascade-off permission work |
| --- | --- | --- | --- |
| Before ORM lookups | Identify ancestry from ViewSet metadata | Select Organization and Customer; Customer is nearest protected | Select Customer only |
| Organization | Load the URL Organization | Check the higher-ancestor requirement, then continue only if allowed | No permission evaluation |
| Customer | Load the URL Customer constrained to Organization | Check nearest-protected requirement, then continue only if allowed | Same nearest-protected check |
| Address | Load the URL Address constrained to Customer | No local permission gate; validate its relationship | Same |
| Instruction endpoint | Continue its normal scoped object/local checks | Keep its local permission/state requirements | Same |

This is the approved interleaving: top-down resolution does not mean loading the entire chain before checking
permissions. Any reached failure stops the walk; no deeper object is examined after an ancestor denial.

## Compatibility and migration

The shared traversal is authoritative for ancestor permissions in both modes. Running the old immediate-parent
gate in addition can contradict the new mapping. Preserve child-object checks, list filtering, inactive-user
handling, and child-create action-state evaluation with the immediate structural parent as its action object.
Nearest-only mode retains an ancestor permission gate for nested Guardian creation, so disabling the cascade
does not require inventing a model-level child-add fallback. All-none ancestry is an explicit policy choice,
not a consequence of disabling cascade. Preserve existing authentication/state responsibilities separately.

Approved P-02 migration rule: reject explicitly supplied removed Guardian parent-permission settings
with actionable errors directing migration to the new declarations. Do not create an automatic translation
layer or preserve a second authorization implementation. The maintainer controls downstream projects.
Defaults formerly supplied by the class are not explicit user declarations. Update existing helpers that
consult removed fields using approved B-05; full navigation parity is deferred. Never silently ignore an
explicitly supplied restrictive old setting.

Default cascading and nearest-change writes are intentional compatibility changes. Document provider defaults,
explicit none, action declarations, and the limits of nearest-only mode. A Breaking changelog entry requires
docs/migrating-1.0.md updates. Under D-49, both release documents must explicitly identify the nested custom
action-entry requirement as a breaking change for core and Guardian applications, including those that have
never used Guardian. Explain the required declarations and configuration-error behavior in both cascade modes.

P-02 migration decision table — **approved**:

| Existing application configuration | Required behavior after migration |
| --- | --- |
| No explicit old parent-policy settings | Use new ancestor policies and requirements; implicit old library defaults do not trigger an error |
| Existing nested generic ActionView, CustomFormView/CustomFormNoObjectView, WorkflowView, or other endpoint without a built-in classification, in a core or Guardian application | Supply an ancestor_policy.actions entry for each endpoint's exact registered key, with a complete nearest/higher pair. Missing entries cause system-check errors and runtime configuration failures in both cascade modes; disabling cascade does not remove this upgrade requirement (D-49) |
| Existing Guardian child views check a parent declared as a core ViewSet | Under the unchanged D-06 defaults, the parent gate becomes model-based instead of object-based. This can remove or grant access. To retain object-based ancestor protection, migrate the parent to GuardianViewSet; provider="guardian" on core ViewSet remains invalid. No automatic compatibility translation or new mixed-composition warning (D-40) |
| Explicit `cv_guardian_parent_permission` or `cv_guardian_parent_create_permission`, including old default values or None | Configuration error naming the removed setting and its replacement; no silent translation |
| Application ViewSet subclass explicitly declares either removed field | Same configuration error; do not let a subclass silently reintroduce ignored policy |
| Cascade disabled under the new configuration | Use the same new mechanism at nearest-protected depth; no old Guardian execution path |
| Existing endpoint view uses `cv_guardian_accept_global_perms` | Retain its endpoint-local role where applicable, but remove its old effect on ancestor checks. To accept model-wide grants at a Guardian ancestor, explicitly set that ancestor's AncestorPolicy.accept_global_perms=True. This is shared ancestor policy, not a per-view override or automatic translation (D-41) |
| Existing nested manage endpoint permits access using only its manage settings/group gate | Normal ancestor authorization and relationship validation now apply as additional requirements. Manage settings/group membership do not bypass them; top-level manage access is unchanged (D-45) |
| Ancestor ViewSet queryset excludes a row that the old model-based parent helper could load | The new ancestor lookup respects that queryset and returns 404 when reached. Review queryset overrides using view: it is the actual requested child endpoint. Reuse the resolved structural parent in request consumers (D-51) |
| Nested application selects a nondefault database through a queryset or routing | Unsupported by first-wave traversal; report a configuration error without stripping or redirecting the selection. default, including explicit using("default"), is supported; existing top-level behavior is unchanged (D-51) |

P-02 does not authorize removing authentication, inactive-user checks, child object/queryset gates, or create
action-state handling. The proposed errors validate declarations without querying the permission database.

### D-49 migration clarification: nested custom endpoint declarations

**Approved after Fable review finding 11.** D-17/B-02 already require explicit ancestor requirements for
nested generic actions, object/no-object custom forms, workflow views, and other endpoints without a built-in
classification. An existing application upgrading to this feature must add those entries even if it uses only
core ViewSets and has never configured Guardian. A missing entry is a configuration failure, reported by
system checks after registration and guarded at runtime; it is not an ordinary permission denial or an inferred
Read operation. Both full cascade and nearest-only mode require the declaration.

For example, a custom Book.publish action beneath Publisher must declare a complete nearest/higher pair under
Book's exact registered publish key in ancestor_policy.actions. Choose the pair for that action's intended
ancestor requirements; neither its HTTP method nor its local permission setting supplies the missing policy.
The entry does not replace independent endpoint-local permissions or other existing checks.

Built-in classified endpoints continue to use their effective Read/Write defaults unless explicitly overridden.
Top-level custom endpoints need no ancestor action entry, and D-47 rejects nonempty actions on their ViewSet.
The eventual feature's Breaking changelog entry and docs/migrating-1.0.md update must explain this scope, the
required declarations, and failure behavior, with an example migration. This is a documentation clarification
of the approved policy; release-document edits accompany implementation rather than claiming it has shipped.

### D-40 migration clarification: Guardian child views beneath a core parent

**Approved after Fable review finding 2.** Today, Guardian child views use Guardian object permissions for
their immediate-parent check even when that parent is declared as a core ViewSet. Guardian grants belong to
model objects independently of the ViewSet class: application code can assign a Publisher object grant while
Publisher is exposed through a core ViewSet. The old Guardian child gate consumes that grant; core Publisher
permission-required endpoints still use their own model-permission checks.

The new traversal instead uses the ancestor's declared provider, with the approved class defaults. This is an
intentional breaking change, including when the application supplied no removed parent-policy settings.
For a read beneath a core Publisher ViewSet, assuming the old strict parent gate, an active authenticated user,
and the same required `view` key:

| Publisher grants held by the user | Old Guardian child parent gate | New core-parent default gate |
| --- | --- | --- |
| Object grant on the URL Publisher only | Pass | Deny |
| Model-wide grant only | Deny | Pass |
| Both | Pass | Pass |
| Neither | Deny | Deny |

These outcomes concern only the parent gate; other selected ancestors and the Book endpoint's independent
object/queryset, actor, and state checks still apply. Passing the parent gate alone does not grant Book access.

To retain object-based ancestor protection, declare Publisher as a `GuardianViewSet`, whose provider defaults
to strict Guardian object permissions. Setting `AncestorPolicy(provider="guardian")` on a core ViewSet is not
a migration path: C-02 rejects it. Retain the core ViewSet when model-based ancestor protection is intended.
The migration changes the ancestor provider, not the independently specified operation requirements; for
example, the new nearest-change write default still applies.

Document this transition explicitly in the Guardian reference, Breaking changelog entry, and
`docs/migrating-1.0.md` when implementing the feature. Do not infer an old provider from the child's registered
views, translate configuration automatically, or introduce a warning merely for mixing a core parent with
Guardian children. That composition remains valid under its model-based ancestor policy.

### D-41 migration clarification: separate ancestor and endpoint fallback

**Approved after Fable review finding 3.** Today a Guardian child view's `cv_guardian_accept_global_perms`
can affect both its local object/queryset gate and its immediate-parent gate. The new mechanism removes the
parent-check role of that flag while retaining its independent endpoint-local behavior where applicable.
It remains a valid view setting and is not rejected as a removed parent-policy declaration.

For Publisher → Book → Note, with Guardian providers on Publisher and Book:

| Setting | Gate it controls |
| --- | --- |
| Publisher's `ancestor_policy.accept_global_perms` | Publisher's ancestor gate when selected for a Book, Note, or other descendant request |
| Book detail view's `cv_guardian_accept_global_perms` | That view's local Book permission gate |
| Book's `ancestor_policy.accept_global_perms` | Book's ancestor gate when selected for a Note or other descendant request; not Book's own endpoint gate |

There is no ViewSet-default → view-override relationship between these settings. An ancestor accepting a
model-wide grant does not relax the child-local gate, and a child view accepting model-wide grants does not
relax a strict ancestor gate. The ancestor fallback remains False by default.

For example, an active user holds model-wide `view_publisher` and an object grant for Book X, but no Publisher
object grant. With the Book detail view's fallback enabled, the old immediate-parent gate passes. Under the
new default Guardian ancestor policy, Publisher's gate denies despite that unchanged Book-view flag.
If model-wide Publisher grants should satisfy the ancestor gate, explicitly configure the Publisher
GuardianViewSet with `ancestor_policy=AncestorPolicy(accept_global_perms=True)`.

That change applies whenever Publisher is selected as an ancestor, not just to the Book view that previously
enabled fallback. Migrating an old per-view preference therefore requires a deliberate shared-policy choice;
do not infer or copy it automatically. It does not bypass other ancestors or endpoint-local gates. Core/model
providers already use model permissions; C-02 still rejects an ineffective ancestor fallback flag on them.

Document the changed scope and possible access loss in the Guardian reference, Breaking changelog entry, and
`docs/migrating-1.0.md` during implementation. Manage diagnostics must distinguish the ancestor fallback from
endpoint-local fallback and must stop reporting a view flag as applicable solely because of the removed
parent-check role. In particular, nested Guardian create must not gain a new child-model-add fallback gate
just to give the retained view flag a role. Existing create semantics remain unchanged.

### B-05 bounded helper migration

**Approved (D-34).** Existing Guardian helpers and diagnostics must stop reading removed settings,
without expanding the first wave into full navigation parity:

| Existing consumer / situation | Required migration behavior |
| --- | --- |
| A helper already checks a resolved immediate structural parent | Use that parent's new provider/fallback policy and the target operation's nearest-ancestor permission requirement |
| That immediate parent explicitly has provider none | Skip its local permission check; keep existing actor/state/custom denials; do not start a new higher-ancestor traversal for rendering |
| Required parent context cannot be established through the helper's existing supported inputs | Retain its existing unavailable/False behavior; do not invent a parent |
| Configuration is invalid | Surface the configuration error; do not convert it to a permissive result or silently hide the mistake |
| Manage diagnostics currently display the removed fields | Display the replacement declared policy, cascade depth, operation requirements, and ancestor fallback, distinctly from endpoint-local Guardian options |
| Manage diagnostics report whether a view's global fallback is applicable | Report only remaining endpoint-local applicability; the removed parent-check role no longer makes the view flag applicable. Display ancestor fallback separately, with no default/override implication (D-41) |

Existing child gates, custom access overrides, and state hooks keep their responsibilities. Existing helpers
may resolve the immediate parent as they do today, including supported single-FK child inputs, but they do
not gain new full-chain navigation queries. If the immediate parent is none, the request may still require a
more distant protected ancestor and deny a destination whose button was shown; that is within the approved
request-only first-wave limitation. Only request enforcement guarantees the selected ancestry was authorized.

Manage reporting must not imply that displaying configuration proves the current user's access to a chain.
Preserve ManageView's local administrative gate. As clarified by D-45, nested manage requests additionally
apply normal ancestor authorization and relationship validation, so their total access can change. Updating
diagnostics does not authorize further manage-access changes or broaden the deferred link/button work.

### Existing code using the settings selected for removal (P-02)

These are current package code/examples, not the replacement API. The maintainer reviewed this walkthrough,
approved P-02, and explicitly requested retaining its code and tables in the design.

The fields are declared on `GuardianViewSet` in
[Guardian viewset.py](../../src/crud_views_guardian/lib/viewset.py):

```python
cv_guardian_parent_permission: str | None = "view"
cv_guardian_parent_create_permission: str | None = None
```

The existing [test application](../../tests/test1/app/views.py) uses them on its **child** Book ViewSet. This
excerpt omits the icon and context-button configuration, but preserves the actual names, relation, and policy:

```python
cv_guardian_book = GuardianViewSet(
    model=Book,
    name="guardian_book",
    parent=ParentViewSet(name="guardian_publisher", attribute="publisher"),
    cv_guardian_parent_permission="view",
    cv_guardian_parent_create_permission="change",
)

class GuardianBookCreateView(CrispyViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
    form_class = BookForm
    cv_viewset = cv_guardian_book

class GuardianBookUpdateView(CrispyViewMixin, GuardianUpdateViewPermissionRequired):
    form_class = BookForm
    cv_viewset = cv_guardian_book
```

For that configuration, the old immediate-parent gate behaves as follows:

| Child Book view | Required Publisher permission from the old parent gate | Independent child permission |
| --- | --- | --- |
| List | view_publisher | Filter rows by view_book grants |
| Detail | view_publisher | view_book on the Book |
| Create | change_publisher | No independent child model-add permission |
| Update | view_publisher | change_book on the Book |
| Delete | view_publisher | delete_book on the Book |

These are permission requirements for the ordinary authenticated active case; other existence, relationship,
state, authentication, and configured global-fallback rules remain. In particular, the old create setting does
not affect update/delete. The newly agreed write default would request change_publisher for those too.

The selector in `GuardianParentPermissionMixin` in
[Guardian mixins.py](../../src/crud_views_guardian/lib/mixins.py) reads those exact fields. This excerpt omits
only the method's docstring:

```python
@classmethod
def _guardian_resolve_parent_perm_key(cls) -> str | None:
    perm_key = None
    if getattr(cls, "cv_permission", None) == "add":
        perm_key = getattr(cls.cv_viewset, "cv_guardian_parent_create_permission", None)
    if perm_key is None:
        perm_key = getattr(cls.cv_viewset, "cv_guardian_parent_permission", "view")
    return perm_key
```

The implementation selects the create override by `cv_permission == "add"`, rather than by a new operation
classification mechanism. `_guardian_user_has_parent_perm()` then resolves this key through the parent
ViewSet's permission map and evaluates it on the resolved parent object; `_guardian_check_parent()` raises
PermissionDenied when that check fails.

Old None/fallback semantics, for the shipped standard child views:

| cv_guardian_parent_permission | cv_guardian_parent_create_permission | Parent check for list/detail/update/delete | Parent check for create |
| --- | --- | --- | --- |
| view | None (library default) | view | view (falls back) |
| view | change | view | change |
| change | None | change | change (falls back) |
| None | change | No parent permission requirement | change |
| None | None | No parent permission requirement | No parent permission requirement |

Both None values are exercised by [test_guardian_parent_none.py](../../tests/test1/test_guardian_parent_none.py).
They skip only the old permission check, not parent existence, authentication, or independent create state.
This is different from the newly agreed cascade-off behavior, which retains the nearest protected gate.

The approved removal is about these two old declarations and their immediate-parent selection semantics.
It is not removal of child Guardian object permissions. Replacement public configuration is specified in
C-01–C-03 above; this historical walkthrough intentionally shows the old fields being removed.

## Performance

Request-local state only. Reuse resolved ancestors and provider checkers where practical, avoiding duplicate
identical Guardian ancestor checks. No persistent permission-result cache. Existing local permission checks
remain independent even if they require separate queries.

Measure one- and three-level chains against current behavior in both cascade modes. Verify no ancestor work
for top-level endpoints and no higher-ancestor permission evaluation in nearest-only mode. Relationship
validation can still require higher-ancestor reads, so nearest-only mode does not imply zero traversal cost.
Report query differences; do not promise zero overhead or impose an
unmeasured fixed cross-backend budget. Explain or remove repeated resolution/checks within one request.

## Acceptance evidence

- Guardian parent plus plain child: global child permission cannot bypass a denied parent.
- Plain child without a local gate still enforces configured ancestors.
- Three-level none-middle case selects the next protected ancestor for change; higher ancestors require view.
- Local child denial still denies; failed ancestor gates cannot be skipped.
- D-42 ordering coverage, after D-43's early actor phase, proves that a reached ancestor denial prevents
  remaining endpoint-local permission checks, child lookup, action-state hooks, form/fragment processing, and
  writes across supported plain, core permission-required, Guardian, manage, and extension compositions.
  Include the B-03 case where an outer
  selected ancestor denies and a deeper object is missing: return 403 without probing the deeper object.
  Also verify that passing ancestry still reaches independent local gates and preserves supported denial
  responses. Tests must observe execution order, not merely assert a final response code.
- D-43 coverage exercises all-none chains with both protected and public endpoints. For actors rejected by
  existing early anonymous/inactive rules, valid, missing, and mismatched ancestry yield the same supported
  denial without ancestor lookup or child processing. Cover login redirect and configured 403/404 behavior.
  Public plain endpoints and supported anonymous-permitting backend/manage configurations acquire no login
  requirement; relationship validation still applies to admitted requests. Protected-ancestry B-01 behavior
  and the later independent child permission/state gates remain intact in both cascade modes.
- Strict change/change and configured view/view writes; reads require view by default.
- Authorized wrong-parent combinations yield 404, including multi-level creates before save/attachment.
- Anonymous, inactive, group-granted, superuser, strict Guardian, and configured global-fallback cases.
- Global/ViewSet precedence; an ancestor's own cascade setting does not remove its contribution to a descendant.
- Cascade disabled retains the nearest protected gate, including through none-policy levels and on creates,
  but does not require higher ancestor permissions. Full relationship validation still applies.
- Unknown custom actions fail checks and runtime guarding; explicit declarations work; misleading keys cannot
  spoof standard classification. Top-level actions need no entry; D-47 rejects ineffective explicit ancestor
  request configuration on their ViewSet.
- Guardian queryset filtering, object gates, create state checks, fragments, and supported M2M cases meet the
  stated contract. Unsupported cases fail clearly. No per-view setting is introduced.
- Resource leaves retain existing list/detail parent scoping beneath one or multiple ORM ancestors in both
  cascade modes. Denied selected ancestors prevent Resource loaders from running; allowed ancestry does not
  waive endpoint-local permissions or application-defined Resource scoping. Resources used as ancestors fail
  checks/runtime guarding; top-level Resources remain unchanged.
- Legacy Guardian settings migration, nearest-only behavior, and request-free UI limitations are documented/tested.
- D-40 migration coverage proves that Guardian child views beneath a default core parent use model permission
  checks: a parent object grant alone denies, and a model grant satisfies that parent gate. Migrating the parent
  to a default GuardianViewSet restores object-based parent protection. Exercise independent child allow/deny
  cases, retain C-02 rejection of guardian provider on core, and require no new mixed-composition warning.
- D-41 migration coverage proves that a child-view fallback cannot relax strict ancestor checks and an ancestor
  fallback cannot relax strict child-local checks. Verify explicit ancestor fallback restores the described
  model-granted parent access, applies consistently across descendant endpoints selecting that ancestor, and
  is reported separately from local fallback in manage diagnostics, including nested create applicability.
- Revocation takes effect on the next request; no persistent authorization cache.
- D-44 coverage rejects constructor-checkable policy errors before registration or automatic manage-view
  creation, preserves existing registry entries, and permits a corrected declaration with the same name.
  Include owning-class/provider/fallback constraints and removed parent-policy constructor/subclass
  declarations. Verify that action-key checks still wait for completed registration and that construction
  validation does not query permission tables.
- D-45 coverage verifies nested core and Guardian manage views require both normal ancestry checks and their
  unchanged local manage gate. Include permissive manage settings with protected ancestry, manage-group
  membership without required ancestor grants, ancestor success with local denial, reached missing/mismatched
  ancestry, both cascade modes, and all-none ancestry under D-43. Top-level manage behavior remains unchanged.
- D-46 coverage verifies nested RedirectChildView uses Read without an explicit action entry, respects normal
  ancestor checks in both cascade modes, and preserves object lookup and any independent local checks.
  Ancestor denial prevents object lookup and redirect processing; an explicit action entry overrides the
  built-in requirements. Following an allowed redirect must still enforce the destination's own ancestor and
  local requirements, including a destination denial after the redirect succeeds. Arbitrary custom redirects
  do not acquire this built-in classification merely because they redirect.
- D-47 coverage rejects non-None cascade/read/write and nonempty actions on ViewSets without a parent, before
  registration under D-44. Cover both boolean cascade values, complete read/write pairs, and a nonempty action
  map without waiting for action registration. Verify clean rejection and corrected-name retry. Omitted and
  explicitly supplied None/empty defaults remain valid; global request defaults do not cause rejection or
  ancestor queries. Valid provider/fallback settings still govern the top-level ViewSet when selected as an
  ancestor, and top-level custom actions need no entry. The same structurally valid request declarations are
  accepted on nested ViewSets, subject to the existing completed-registry checks.
- D-48 coverage verifies that a nested ViewSet with only card registered accepts a card override and rejects
  an unregistered list key after registration completes, even though navigation can resolve list to card.
  When both views exist, each override affects only its own endpoint. A CardListView explicitly registered
  under list accepts that exact key and retains its Read family. Without an override, normal Read requirements
  apply. Preserve navigation fallback and prove that reaching card through it still uses the card endpoint's
  own override; adding a real list view must not retarget the existing card override.
- D-49 release documentation explicitly names the nested custom action-entry requirement in the feature's
  Breaking changelog entry and docs/migrating-1.0.md, covering core and Guardian applications, both cascade
  modes, exact registered keys, complete permission pairs, and system-check/runtime failure behavior. Include
  a migration example and the built-in/top-level exceptions. Existing unknown-action acceptance coverage must
  prove the missing-entry failure and successful explicit declaration for both application types and modes.
- D-51 coverage proves that ancestor ViewSet queryset filters constrain nested requests, including a
  soft-deleted or tenant-excluded row with an otherwise-valid grant, and that no unfiltered retry occurs.
  Exercise both cascade modes, none-policy ancestors, and filters supplied by the manager used by the
  queryset. Verify the actual child view/request/kwargs are passed, ancestor view-specific overrides are not
  invoked, and B-03/D-43 denials prevent later queryset calls. Create attachment and parent-based state checks
  use the same resolved structural parent identity, including when it is not the nearest protected ancestor.
  Cover default and explicit using("default"), and reject nondefault queryset/routing selections for the
  supported nested paths without rerouting. Use overlapping PKs in default/shard fixtures to expose accidental
  fallback. Preserve existing top-level database behavior. Do not treat the existing superuser-only nondefault
  queryset test as evidence of supported nondefault ancestor authorization.
- D-52 boundary examples/coverage include a child shared by two parents and an update form exposing its parent
  FK. With URL ancestry and local gates satisfied and no additional application restriction, a shared-row edit
  remains visible through the other parent, and a valid FK change is not automatically blocked or given a
  destination-parent authorization check. Explain the application's responsibility for any stronger isolation
  and illustrate an application-owned restriction. Preserve standard deletion rather than silently unlinking;
  full cascading does not add all-membership traversal. Cover the same boundary in both cascade modes.
- D-53 coverage exercises self-cycles, two-ViewSet cycles, and missing parent references through actual
  urlpatterns/URLconf construction, as well as direct system checks and supported request safeguards. Require
  bounded, actionable failures identifying the affected configuration, without database queries or an
  unbounded parent walk. Verify that a valid child-before-parent declaration generates URLs once the parent
  is registered. Relevant ancestry helpers must also terminate safely; an isolated request-guard test is not
  sufficient evidence that startup/import is safe.

Tests should prove boundaries, not mirror helper code. Use bounded multicore pytest for broad runs and the
appropriate repository framework matrix during implementation. No implementation or tests have run for this draft.

## Builder discretion and maintainer review

The builder may decide private module layout, private names, static check IDs, standard
operation classification mechanics, request-local storage, and the entry point, within the stated contract.

P-01 precedence, P-02 removed-setting errors, and P-03 relationship scope are approved. Provider
defaults, the optional Guardian fallback, request-only scope, and both cascade depths are confirmed.

## Builder review disposition

A fresh builder review identified migration, provider-default, navigation-scope, relationship-boundary, and
global-precedence questions. The maintainer then clarified that the switch exists for performance and selected
full cascading versus nearest-protected-only checks. That supersedes the draft's former total opt-out, legacy
fallback, and disabled-create fallback proposals. Those alternatives remain only in the discussion history.

The provider defaults, optional Guardian global-permission fallback (off by default), and request-only first
wave have since been confirmed. Full button/link visibility consistency is deferred. The explicit
removed-setting error is now approved as P-02; there is no need for two execution paths.
P-03's original blanket nested-Resource exclusion was subsequently superseded by D-39: retain Resource leaves
under ORM ancestry, with their existing application-defined scoping; reject Resource ancestors. Nearest-only
mode is not an escape hatch for unsupported relations. B-01–B-05 and the concrete API decisions C-01–C-03 are
approved and recorded in the GSD handoff. The consolidated design has final maintainer approval (D-38), with
the D-39 amendment; planning is explicitly deferred.

### Fable review disposition: Resource leaves

On 2026-11-07 the maintainer approved the Resource-leaf proposal from finding 1 of the
[Fable review](2026-11-07-ancestor-authorization-design-code-review-fable.md). D-39 records the amendment and
its division of responsibility between shared ORM ancestor enforcement and application-defined Resource
membership. The original D-29 restriction remains recorded as superseded. Findings 2–12 have the approved
dispositions below; all twelve Fable findings are resolved at the design-document level.

### Fable review disposition: core-parent migration

On 2026-11-07 the maintainer accepted finding 2 as a migration-documentation gap, recorded as D-40.
D-06's provider defaults and C-02's requirement to use GuardianViewSet for a guardian provider remain unchanged.
The migration table and explanation now identify both access loss and access gain for existing Guardian child
views beneath a core parent, and the parent-class migration needed to retain object-based protection.
Acceptance coverage must prove the changed default, migration path, and independent child gates. No automatic
compatibility translation or new mixed-composition warning is approved.

### Fable review disposition: independent fallback settings

On 2026-11-07 the maintainer approved finding 3's migration and diagnostics clarification, recorded as D-41,
after confirming that the view-level flag is not an override of the ViewSet ancestor policy. D-18's separation
remains unchanged. The migration guidance now records the removed parent-check role, explicit ancestor-side
replacement, and shared scope across descendant endpoints. Diagnostics and acceptance criteria must prove
the two settings remain independent.

### Fable review disposition: enforcement order

On 2026-11-07 the maintainer accepted finding 4 as an integration-order clarification, recorded as D-42.
The approved resolution makes B-03's order explicit across all supported shipped compositions and rules out
placing the only check in `CrudView.dispatch()`. Small explicit bridges into one shared authorization
implementation remain acceptable; the exact integration hook is deferred to implementation planning.
Existing local permission/state checks and supported denial responses must be preserved. Acceptance evidence
must show that ancestor denial prevents downstream processing, not just that the final response is a denial.
No new permission policy or particular `as_view()`/`setup()` implementation is approved. D-43 below subsequently
refines the early actor phase without moving child-object or state processing before ancestry.

### Fable review disposition: early actor denials with all-none ancestry

On 2026-11-07 the maintainer approved finding 5's resolution and requested a documentation commit. D-43
preserves endpoint early anonymous/inactive denials before ancestor lookup even when no protected ancestor
is selected, closing the proposed ordering's existence-disclosure gap. It adds no authentication restriction
to otherwise-public all-none endpoints and preserves supported backend/manage behavior. B-01/B-03 and D-42
are refined explicitly: static validation first, applicable early actor checks next, then ancestor resolution
and authorization, followed by remaining local checks and processing.

### Fable review disposition: clean construction-time rejection

On 2026-11-07 the maintainer approved finding 6 and requested a documentation commit. D-44 requires policy
constraints decidable during construction to be checked before ViewSet registration and automatic manage-view
creation. Rejection must leave no registration behind and a corrected declaration must be able to reuse the
name. Checks needing completed registration remain at their later stage. The preferred approach is validation
before registration; exact validator arrangement remains an implementation choice. Acceptance criteria cover
clean rejection, successful retry, and preservation of deferred checks.

### Fable review disposition: nested manage access

On 2026-11-07 the maintainer approved finding 7's clarification and requested a documentation commit. D-45
retains manage's Read classification and explicitly distinguishes its unchanged local access rules from the
additional ancestor and relationship requirements on nested requests. Manage settings/group membership are
not an ancestor bypass; all-none and top-level cases retain their stated boundaries. The exemption alternative
is not adopted. Migration guidance and acceptance criteria record the total-access change.

### Fable review disposition: built-in child redirects

On 2026-11-07 the maintainer approved finding 8's resolution and requested a documentation commit. D-46 adds
RedirectChildView to B-02 as Read: normal ancestor authorization and relationship validation precede its
existing object lookup and redirect processing. No action entry is required merely for using this built-in
family; explicit action overrides remain supported. Local checks stay independent, and the destination
enforces its own requirements on its request. The resolution does not infer a family for arbitrary redirects
or custom actions. The operation table, acceptance criteria, and source addendum record this bounded addition.

### Fable review disposition: ineffective top-level request settings

On 2026-11-07 the maintainer approved finding 9's resolution and requested a documentation commit. D-47
rejects non-None cascade/read/write and nonempty actions on a ViewSet without a parent. None/empty defaults
remain valid; provider and accept_global_perms retain their meaning and existing validation rules. These
request settings do not flow down to descendants: requirements for Book requests belong on Book, not its
top-level Publisher. The validation happens before registration under D-44, without resolving action keys or
querying permission tables. Global request defaults remain valid. The API table, explanation, acceptance
criteria, and source addendum record the rule.

### Fable review disposition: exact action keys

On 2026-11-07 the maintainer approved finding 10's resolution and requested a documentation commit. D-48
requires exact registered view keys for both ancestor action validation and override resolution. The list-to-card
navigation fallback does not make an unregistered list key valid in actions. Separate registered list/card
views retain separate overrides; a card view actually registered as list accepts that key. Normal built-in
Read classification and existing navigation aliases remain intact. The API and validation tables, operation
rules, acceptance criteria, and source addendum record the distinction.

### Fable review disposition: custom endpoint migration documentation

On 2026-11-07 the maintainer approved finding 11 as a migration-documentation clarification and requested a
documentation commit. D-49 preserves the approved explicit-declaration requirement for nested custom
endpoints and identifies its upgrade impact on core and Guardian applications in both cascade modes. The
migration table and explanation now name the required action entries and system-check/runtime configuration
failures. Acceptance criteria and the source addendum require the eventual feature's Breaking changelog and
docs/migrating-1.0.md updates to explain the migration, including built-in and top-level exceptions. No new
permission policy is introduced.

### Fable review disposition: public-module example import

On 2026-11-07 the maintainer approved finding 12's example-only cleanup and requested a documentation commit.
D-50 updates the C-01 example to import ParentViewSet alongside the other ViewSet configuration types from
crud_views.lib.viewset, which already exports ParentViewSet. The previous submodule import remains valid;
this is documentation consistency, with no permission or API behavior change. All twelve Fable findings now
have approved dispositions, recorded in D-39–D-50. Original review findings remain preserved; planning and
implementation remain deferred.

### Astra review disposition: ancestor queryset scope and identity

On 2026-11-07 the maintainer approved F-01's revised resolution, recorded as D-51, and subsequently requested
a documentation commit before discussing F-02. The discussion rejected
preserving model-manager-only ancestor lookup because developers expect ViewSet soft-delete and tenant
filters to constrain descendant access. Resolve through the ancestor ViewSet's queryset with the actual
requested view as context, preserve relationship checks, and reuse the resolved structural parent. No
unfiltered fallback or synthetic ancestor view is introduced. The maintainer chose to defer nondefault and
cross-database support: default-only nested traversal rejects incompatible selections instead of ignoring
using(...) or routing. Existing top-level database behavior remains intact. The request contract, validation
and migration tables, acceptance evidence, and source addendum are reconciled with this decision.

The [Astra review](2026-11-07-guardian-child-permissions-design-review-astra.md) preserves its original findings
and records this disposition separately. F-02/F-03 resolutions follow below. All three Astra findings are
resolved at the design-document level; planning and implementation remain deferred.

### Astra review disposition: URL-path mutation boundary

On 2026-11-07 the maintainer approved F-02's scope clarification and requested a documentation commit. D-52
retains URL-path ancestor authorization, with additional protection for shared-object writes, parent changes,
and effects outside the path owned by the endpoint/application. The discussion used a Genre shared by two
Guardian-protected publishers and a Book update form that permits changing its publisher. Passing ancestry
and local checks does not supply checks on another parent or guarantee container isolation. The scope table,
request continuation, acceptance examples, and source addendum now state that boundary. Standard save/delete
semantics are preserved, including deletion rather than automatic unlinking. No new mutation-policy engine or
automatic parent-change restriction is approved. Planning and implementation remain deferred.

### Astra review disposition: safe validation before URL construction

On 2026-11-07 the maintainer approved F-03's validation-timing clarification and requested a documentation
commit after discussing its implementation cost. D-53 requires cycles and missing references to fail safely
at or before URL construction can enter an unbounded parent walk, with the existing system-check/request
safeguards retained. The check uses registration metadata, identifies the affected configuration, and
preserves valid forward references during registration. A small shared structural mechanism is preferred;
exact helper arrangement remains implementation discretion. The validation table, request prerequisites,
acceptance criteria, and source addendum record the requirement. All three Astra findings now have approved
dispositions in D-51–D-53; original findings remain preserved. The review decisions are ready for design-v2
consolidation. Planning and implementation remain deferred.

## Design approval boundary

The preceding discussion selected behavior and an approach, not implementation. P-01 precedence, P-02 migration,
and P-03 relationship/Resource scope as amended by D-39 are approved, along with B-01–B-05 and C-01–C-03.
The original product/API decisions are settled, and all twelve Fable review findings have approved
dispositions in D-39–D-50. Resolving the documentation review does not authorize planning or implementation.
D-51–D-53 resolve all three Astra findings. All review dispositions are recorded for design-v2 consolidation.
The maintainer has given final spec approval and instructed that no
plan be written yet (D-38). Unsupported cases
must not be silently exempted in either cascade mode.

No production code, dependency installation, or test execution has occurred for this design. The maintainer
authorized documentation commits: C-01/C-02 in `db4c2cc6`, and C-03/status reconciliation in `27102355`.
The final-approval record does not imply another commit. Planning is the next workflow only when the
maintainer requests it; do not invoke writing-plans or create a plan now. Implementation has not begun.

## Technical addendum: resuming in a fresh context

### A. Status, evidence, and reading order

This addendum records source inspection, not implemented behavior or runtime verification. No new traversal
classes/settings exist yet. No test suite, benchmark, dependency installation, or application migration was
run for this design. The separate application analysis also read tests without executing them.

Source references were refreshed on 2026-11-07. At that inspection the checkout was on
`gsd/phase-06.17-object-detail-open-the-first-accordion-group-and-initialize`, HEAD
`5f70a2f69ae4622551e94b4b8e4ad58c540315b4`, with unrelated local changes. This feature is NOT assigned to that
phase or branch. Other work changed the checkout during the discussion; verify current status before editing
and preserve unrelated changes. Symbol names below are more durable than line numbers.

Resume in this order:

1. Read repository [CLAUDE.md](../../CLAUDE.md), this document's GSD ledger, then its current design sections.
2. Final design approval is recorded in D-38, with review resolutions in D-39–D-53. Check for a subsequent
   instruction to begin planning and any phase assignment; do not infer either from spec approval.
3. Inspect the named symbols below at the current revision. Use the chronological
   [discussion](2026-11-07-guardian-child-permissions-discussion.md) for rationale, not superseded defaults.
4. Preserve P-01–P-03 (including D-39's Resource-leaf amendment), B-01–B-05, and C-01–C-03; all are approved.
   Resolve only new evidence-backed conflicts.
   Ordinary engineering choices belong to the implementer under the maintainability constraint.
5. Do not write a plan yet: the maintainer explicitly deferred planning when approving the spec. After a
   subsequent instruction to plan, use the authorized workflow. If using GSD, carry the ledger into the
   assigned phase context. Prior documentation commits do not authorize implementation.

### B. Core registry, URL ancestry, and permission vocabulary

| Source | Existing symbols | Relevant behavior / implementation caution |
| --- | --- | --- |
| [viewset/__init__.py](../../src/crud_views/lib/viewset/__init__.py) | `ViewSet`, `_REGISTRY`, `_REGISTRY_LOCK` | ViewSet is a Pydantic model with a process-global named registry. Snapshot/restore it in dynamic tests. |
| Same | `register()`, `register_view_class()`, `get_all_views()`, `get_view_class()` | Registration happens during configuration/class definition. Core automatically registers a manage view for ORM ViewSets. D-44 requires constructor-checkable policy validation before these side effects. Do not load ancestors or query permission grants here. |
| Same | `is_view_registered()`, `get_view_class()`, `get_router_name()` | is_view_registered checks literal keys; the latter two fall back from list to card when no list exists. D-48 requires exact registered keys for ancestor action validation/override lookup. Successful navigation resolution does not prove literal registration; preserve the navigation fallback. |
| Same | `parent`, `pk_name`, `get_parent_url_args(first_only=False)`, `get_parent_model()`, `get_parent_attributes()` | Parent chains are already represented explicitly. With `first_only=True`, these helpers concern the immediate structural parent, not the nearest protected ancestor. |
| Same | `get_queryset(view)` | Walks ParentViewSet links, constructs joined relation filters from URL parent PKs, and queries the child model. It validates child/ancestor relationships for object lookups but performs no parent authorization. |
| Same | `get_path_parent()`, `urlpatterns` | Generate nested URL patterns; URL resolution names an endpoint, it does not execute ancestor endpoints. Top-level and nested ViewSets can target the same model. |
| Same | `default_permissions`, `permissions`, `_default_permissions` | Core resolves the model ContentType and Permission rows, removes only the `_<model>` suffix from codenames, and caches nonempty permission maps. Empty discovery is retried after migrations. This is permission vocabulary, not cached user access. |
| [parentviewset.py](../../src/crud_views/lib/viewset/parentviewset.py) | `ParentViewSet` | Fields: `name`, `attribute`, `pk_name`, `many_to_many_through_attribute`. `viewset` resolves through the registry. |
| Same | `get_pk_name()`, `get_attribute()` | Default URL parent argument is `<parent ViewSet name>_pk`; default relationship attribute is the parent ViewSet name. Explicit overrides are common and must win. |
| [view/meta.py](../../src/crud_views/lib/view/meta.py) | `CrudViewMetaClass.__new__()` | A class with its own `cv_viewset` registers under its `cv_key`; model is populated if absent. Avoid registration/import side effects for request authorization. |

Keep these three identifiers separate: ViewSet registry name, model relationship attribute, and URL argument
name. Never guess that they match. In an existing test the parent registry name is generated, but the Book FK
is still `publisher`. Parent models can have int or UUID PKs; no integer coercion assumption is safe.

Existing chain walkers do not prove cycle safety. ViewSet.urlpatterns calls get_path_parent() before creating
request callables, and URLconf import can reach that unbounded parent loop before later checks. D-53 requires
safe structural validation at or before URL construction and safe termination of other supported ancestry
walks, alongside check/request safeguards. Reject cycles and missing references with actionable errors using
registration metadata only. Permit child-before-parent declarations until resolution is needed; valid forward
references work once registration is complete. Reuse a small structural mechanism rather than constructing a
second independent URL-routing or parent-inference system.
For M2M, use declared relationships and actual membership; a child alone may not identify one parent.

### C. Core request and local authorization path

Read [view/base.py](../../src/crud_views/lib/view/base.py):

- `CrudView` is a mixin using `CrudViewMetaClass`, not a standalone Django view. Concrete view classes combine
  it with Django generic views. `CrudView.dispatch()` currently consumes cancel-restore state, delegates with
  `super()`, and adds modal response Vary handling. Preserve those responsibilities.
- `CrudView.get_queryset()` delegates to `self.cv_viewset.get_queryset(view=self)`.
- `CrudView.cv_get_parent_object()` resolves only the immediate parent by URL PK with `get_object_or_404`.
  It neither authorizes that object nor verifies the full ancestor chain around it.
  This describes the existing implementation. D-51 requires supported nested request consumers to reuse
  the structural parent resolved through its ancestor ViewSet queryset, including create attachment and state
  checks; do not keep this model-based lookup as a second request-resolution path after traversal succeeds.
- `cv_get_parent_object_attribute()` uses the configured immediate relation. Do not replace its structural
  meaning with nearest-protected-ancestor semantics: creation must attach to the actual structural parent.
- `CrudViewPermissionRequiredMixin` extends Django `PermissionRequiredMixin`. Its cached `permission_required`
  property maps `cv_permission` through the endpoint ViewSet and currently asserts if the key is missing.
- `CrudViewPermissionRequiredMixin.has_permission()` first runs the model permission check, then resolves
  `cv_get_action_object()` and invokes `cv_action_enabled(user, obj)` as a separate state gate.
- Core `cv_has_access(user, obj)` on the permission mixin uses model permissions. Plain `CrudView.cv_has_access`
  does not turn the view into a permission-required endpoint. Access helpers are not request interception.
- `cv_get_action_object()`, `_cv_action_enabled_for_context()`, and `_cv_action_enabled_for_rendering()` serve
  different request/rendering contexts. Do not treat action state as a substitute for authorization.

Representative source-level execution shapes (not runtime traces):

| Composition | Existing gate placement |
| --- | --- |
| Plain core view | `CrudView.dispatch()` then Django handler; no automatic core model permission mixin |
| Core permission-required view | Django permission dispatch always precedes `CrudView.dispatch()` in shipped compositions and calls `has_permission()`; its state check may load the endpoint object, and denial can prevent reaching CrudView.dispatch() at all |
| Guardian object child | Parent mixin dispatch first; Django permission dispatch uses Guardian's bypassing `has_permission()`; object permission/state checked through `get_object()` |
| Guardian list child | Parent dispatch gate, then queryset filtering through `GuardianQuerysetMixin.get_queryset()` |
| Guardian create child | Parent dispatch gate authorizes creation; no separate model-level child-add requirement |
| Built-in manage view | Django permission dispatch precedes `CrudView.dispatch()` and calls the manage view's own `has_permission()` |

This MRO ordering is a primary integration constraint under D-42. Putting the only new check in
`CrudView.dispatch()` cannot satisfy B-03 for the shipped permission-required compositions. Trace supported
MROs before choosing the shared enforcement entry point, including Guardian's earlier dispatch path and the
manage view's distinct permission method. Small explicit bridges may call the same implementation; do not
introduce a chain of hidden interception hooks or duplicate authorization logic. Document cooperative
requirements for custom overrides.

Django's `View.as_view()` calls `self.setup(...)` and then `self.dispatch(...)`; it ignores setup's return
value. Merely returning a redirect from `setup()` cannot short-circuit the request. This is an implementation
constraint, not selection of an `as_view()` wrapper or another hook. The eventual integration must support
the approved login/denial responses as well as exception-based denial.

### D. Existing Guardian enforcement and migration dependencies

Read [Guardian mixins](../../src/crud_views_guardian/lib/mixins.py):

| Symbol | Current behavior that matters |
| --- | --- |
| `_guardian_inactive_actor(user)` | Explicitly denies inactive authenticated users because Guardian queryset behavior alone is insufficient, including for inactive superusers. Anonymous handling is separate. |
| `GuardianObjectPermissionMixin.has_permission()` | Handles authentication/inactivity, then permits the request to reach the object gate instead of requiring a model permission. |
| `GuardianObjectPermissionMixin._check_object_perm()` | With global fallback enabled, checks `user.has_perm(full_permission)` first; otherwise/then uses `ObjectPermissionChecker` on the object. |
| `GuardianObjectPermissionMixin.get_object()` | Delegates to the normal scoped object lookup, checks the child's object permission, then its action-state gate. Preserve this independent protection. |
| `GuardianObjectPermissionMixin.cv_has_access()` | Object-oriented rendering/access helper; not a substitute for ancestor traversal. |
| `GuardianQuerysetMixin.get_queryset()` | Filters the scoped queryset through `get_objects_for_user`, with `accept_global_perms` from the view and `use_groups=True`; inactive actors get none. |
| `GuardianQuerysetMixin.has_permission()` / `cv_has_access()` | List admission is not evidence that any particular row is visible; filtering is the child gate. |
| `GuardianParentPermissionMixin.dispatch()` | Validates composition, handles anonymous/inactive actors, checks the immediate parent, then delegates. It does not recurse through higher ancestors. |
| `GuardianParentPermissionMixin.has_permission()` | Returns True for nested views after composition validation, intentionally bypassing core model-level permission checks. At top level it delegates. |
| `_guardian_resolve_parent_perm_key()` / `_guardian_parent_perm_key()` | Select the old parent key; `cv_permission == "add"` selects the create override, whose None falls back to the ordinary parent key. |
| `_guardian_user_has_parent_perm()` | Checks the selected parent permission; currently reads the child view's global-fallback option. A None key skips permission evaluation, not parent existence/state processing. |
| `_guardian_check_parent()` | Resolves the immediate parent, checks permission, and applies `cv_action_enabled(user, immediate_parent)` for no-object child views. |
| `_guardian_child_composition_error()` / `_guardian_validate_child_composition()` | Reject missing child object/queryset gates and unreachable MRO placement. Do not remove these protections just to allow a plain child under the new shared traversal. |

The old composition guard belongs to old Guardian view composition. The new shared ancestor mechanism must
also work with plain core views without requiring a Guardian child-object gate. Those facts are compatible:
do not weaken `Guardian*PermissionRequired` local checks or fix the problem merely by deleting the old guard.

Read [Guardian ViewSet](../../src/crud_views_guardian/lib/viewset.py):

- Existing fields are `cv_guardian_parent_permission="view"` and
  `cv_guardian_parent_create_permission=None`. Both currently belong to the child ViewSet and describe its
  immediate-parent check. The new ancestor provider declaration instead belongs to the ancestor itself;
  the endpoint ViewSet's operation requirements decide which keys to request. This is a real migration.
- `GuardianViewSet.default_permissions` uses `guardian.ctypes.get_content_type`, unlike core's ordinary
  ContentType resolution. Preserve Guardian-configured proxy/polymorphic identity semantics.
- `GuardianViewSet.get_objects_for_user()` has a fixed strict policy in `STRICT_HELPER_POLICY`. The new ancestor
  fallback option must not silently change this helper's contract or existing local view policies.
- `assign_perm()`, `remove_perm()`, and `_resolve_permission_key()` provide examples of explicit permission-key
  validation. They are not new traversal callbacks.
- `reject_removed_global_perms_flag()` already rejects the removed ViewSet-level
  `cv_guardian_accept_global_perms` constructor key with a Pydantic before-validator. Existing view-level use
  of that name remains supported. Do not accidentally reintroduce the removed ambiguous option name for the
  new, independently scoped ancestor fallback without an explicit API/migration decision.
- `register()` rejects Resource models and replaces the auto-created core manage view with Guardian's variant.

**Global-permission fallback trap:** Django's model backend does not supply global grants just because an
object is passed to `has_perm`. Follow the existing separate model-permission check plus object check. One
existing Guardian mixin docstring suggests otherwise; implementation and tests are the evidence to follow.

Read [Guardian views](../../src/crud_views_guardian/lib/views.py):

- Shipped detail/update/action views combine `GuardianParentPermissionMixin`, `GuardianObjectPermissionMixin`,
  and their core permission-required view. List/card variants combine the parent and queryset mixins.
- `GuardianCreateViewPermissionRequired` combines the parent mixin and core `CreateViewPermissionRequired`.
  Its nested path intentionally bypasses child model add permission. Top-level create still requires add.
- `_cv_guardian_create_parent()` resolves either the parent instance or a configured single-FK own-child
  instance. It rejects ambiguous M2M child-only inputs. Do not guess an M2M parent for an access helper.
- `cv_create_has_access()`, `cv_has_access()`, and `_cv_action_enabled_for_context()` distinguish parent
  permission, create visibility, and action state. Custom `cv_create_has_access()` is not itself a request gate.

Search all references to the old keys/methods before removal. Current consumers beyond dispatch include:

| Consumer | Symbols / path |
| --- | --- |
| Collection/child link access | `GuardianQuerysetMixin._cv_child_link_has_access()` |
| Create button context from a list | `GuardianQuerysetMixin.cv_get_context()` resolves URL parent and calls `cv_create_has_access()` |
| Cancel target availability | `GuardianParentPermissionMixin._cv_cancel_target_available()`, `_cv_cancel_parent_target_access()` |
| Create access helpers | `GuardianCreateViewPermissionRequired.cv_create_has_access()`, `cv_has_access()` |
| Manage diagnostics | `GuardianManageView.get_context_data()`, `get_view_data()`, `_guardian_global_fallback_applicable()` |
| Manage template | [guardian/config_table.html](../../src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html) reads both old parent fields |
| System checks | [Guardian checks](../../src/crud_views_guardian/checks.py), `check_guardian_composition()` / `crud_views_guardian.E001` |

Wave-one request-only scope does not mean these consumers can be left reading removed attributes. Keep their
migration bounded; it does not authorize broad ancestor parity in all navigation. If a removed-field helper
cannot be adapted without choosing a new observable behavior, document the precise conflict instead of
silently widening the wave.

### E. Create, actions, fragments, and extension families

D-52 preserves the mutation boundary in these paths. UpdateView.cv_form_valid() saves the submitted form;
ancestor validation does not pin an editable parent FK or authorize a replacement parent. Updates/deletes of
shared M2M objects retain their normal effects on the shared row. Custom actions own any authorization needed
for effects beyond the URL ancestry. Document these boundaries without introducing all-membership traversal,
automatic unlinking, or a generic mutation-policy engine.

- [create.py](../../src/crud_views/lib/views/create.py): `CreateView.cv_form_valid()` saves the form instance.
  `CreateViewParentMixin.cv_form_valid()` attaches the immediate structural parent through the configured FK,
  or saves and adds the M2M relationship using `many_to_many_through_attribute` and
  `cv_parent_many_to_many_through_defaults()`. Parent permission selection must not change that attachment.
  A create request needs ancestor-to-ancestor relationship validation before writing; no existing child row
  is available to make `get_queryset()` prove the whole chain.
- [views/mixins.py](../../src/crud_views/lib/views/mixins.py): `CrudViewProcessFormMixin.post()` resolves an
  object if applicable, builds context, calls `cv_post_hook()`, validates, and invokes `cv_form_valid_process()`.
  That method runs save/hook work inside `cv_get_atomic()` and schedules `cv_on_commit()`. Ancestor denial must
  precede hooks/rendering/write work; do not relocate authorization into form validity alone.
- [action.py](../../src/crud_views/lib/views/action.py): `ActionView.post()` gets the object and calls
  `cv_action_process()`, which wraps `action()` and hooks in the existing transaction path. Generic
  `ActionViewPermissionRequired.cv_permission="change"` is not enough to infer its ancestor policy: custom
  actions require the explicit ViewSet declaration under D-17.
- [form.py](../../src/crud_views/lib/views/form.py): `CustomFormView`, `CustomFormNoObjectView`, and their
  PermissionRequired variants cover object/no-object custom forms; the permission variants default to view.
  That default is not proof that the form is read-only. Require the declared custom-action policy.
- [formsets/mixins.py](../../src/crud_views/lib/formsets/mixins.py): `FormSetMixinBase.get()` handles
  `?template=...` fragments, loading `self.object` through `get_object()` when applicable before
  `get_template_html()`. No-object fragments rely on earlier dispatch gates. Preserve this authorization order.
  `FormSets._cv_validate_fragment_coordinates()` in [formsets.py](../../src/crud_views/lib/formsets/formsets.py)
  validates fragment ancestry/prefixes against the editor root; do not confuse it with URL ViewSet ancestry.
- [card.py](../../src/crud_views/lib/views/card.py): `CardListView` derives directly through `CrudView` and
  Django's ListView, not the package's `ListView` subclass. Standard read-family classification must include it.
- [child.py](../../src/crud_views/lib/views/child.py): `RedirectChildView` combines CrudView, SingleObjectMixin,
  and Django RedirectView. It loads the current object and resolves a child URL without itself mutating data.
  D-46 classifies the shipped family as Read; ancestor enforcement precedes its object lookup and redirect.
  Preserve local checks, and let the destination independently enforce its own requirements on its request.
- [ObjectDetail views](../../src/crud_views_object_detail/lib/views.py): `ObjectDetailView` extends core DetailView;
  retain read semantics through presentation mixins.
- Polymorphic [create](../../src/crud_views_polymorphic/lib/create.py),
  [detail](../../src/crud_views_polymorphic/lib/detail.py),
  [update](../../src/crud_views_polymorphic/lib/update.py), and
  [delete](../../src/crud_views_polymorphic/lib/delete.py) extend corresponding core families.
  [create_select.py](../../src/crud_views_polymorphic/lib/create_select.py) instead defines
  `PolymorphicCreateSelectView(CrudView, generic.FormView)`: B-02 explicitly classifies it as Write, even though
  it does not inherit core CreateView.
- [Workflow views](../../src/crud_views_workflow/lib/views.py): `WorkflowView` extends CustomFormView, and
  `WorkflowViewPermissionRequired` uses local change permission. Keep transition/state checks independent;
  approved B-02 requires an explicit ViewSet ancestor declaration rather than inferring workflow intent.
- [Resource](../../src/crud_views/lib/resource.py): `ResourceViewMixin` must precede the core view in MRO. It
  overrides `get_queryset()` and `get_object()` with `cv_get_items()` / `cv_get_item()` and passes URL kwargs;
  it does not inherit ORM parent scoping. Under P-03 as amended by D-39, Resource leaves remain supported below
  ORM ancestors. Shared traversal validates and authorizes those ancestors before Resource loading; Resource
  membership stays application-defined through the existing URL kwargs contract. Resources cannot be ancestors.
  Top-level Resources must not acquire irrelevant ancestor requirements.

### F. Settings, checks, failures, and caching

Settings live in [settings.py](../../src/crud_views/lib/settings.py): `from_settings()`, `CrudViewsSettings`,
and the module singleton `crud_views_settings`. Many values are captured at import; tests commonly monkeypatch
the singleton instead of assuming Django `override_settings` updates it. Follow a deliberate existing pattern
for the new global setting and document it; do not accidentally mix live reads and frozen values.

Core [checks.py](../../src/crud_views/checks.py) registers `check_viewsets()` under `crud_views` and calls
`ViewSet.checks_all()`. [check.py](../../src/crud_views/lib/check.py) supplies Check classes and the W280
unknown-attribute vocabulary cache `_VOCAB_CACHE`. `CrudView.checks()` and
`CrudViewPermissionRequiredMixin.checks()` contribute class checks. Choose unused IDs, and do not broaden
the unknown-attribute exemption just to hide new declaration mistakes.

Static structure validation must work before migrations. Accessing `ViewSet.permissions` can query ContentType
and Permission tables; that is not an import-safe way to validate every action. Separate static declaration
validation from runtime permission resolution, with deterministic errors when tables/keys are unavailable.
Do not replace an unknown key with a weaker key or skip the ancestor. Current permission-map caching is a
different concern from prohibited cross-request authorization-result caching.

D-47's top-level constraint is decidable from the owning ViewSet's parent declaration and declared policy
values, so apply it before registration under D-44. Reject non-None cascade/read/write and nonempty actions
without looking up parent ViewSets, registered action keys, or permissions. Do not apply that restriction to
global defaults or to ancestor-side provider/fallback settings; those retain their existing validation rules.

Anonymous/denied behavior is specified by approved B-01/D-30 and failure ordering by B-03/D-32. Guardian has
`cv_guardian_anonymous_behavior` values redirect/403/404; plain views need a supported denial path without
assuming AccessMixin, with standard login redirect as the default. Preserve existing configured endpoint
responses and authentication/inactive-user protections separately from the removable legacy parent gate.

D-51 settles the first-wave database boundary: new nested traversal supports only default for ORM ancestry,
any ORM child data, and relevant authorization records. Validate queryset/routing selections and surface a
configuration error for a nondefault alias; never silently force default or remove using(...). Explicit
using("default") is valid. Existing routed/content-type tests provide fixtures for rejection and preservation
of top-level behavior, not a promise of nondefault ancestor support. Do not introduce a routing API or a
cross-database identity framework. Ancestor queryset scope and resolved parent identity are specified in the
D-51 request contract above; neither is left to implementation discretion.

### G. Existing tests and reusable fixtures

The following are source pointers, not claims that these suites passed in this session:

| Test file | Useful contract / reuse |
| --- | --- |
| [test_authorization_matrix.py](../../tests/test1/test_authorization_matrix.py) | Role/permission/request matrix, strict and fallback families, parent overrides, isolated routes, no-write assertions |
| [test_fragment_authorization.py](../../tests/test1/test_fragment_authorization.py) | Denied fragments must not render HTML or evaluate secret field choices; create/object paths; wrong-parent and inactive cases |
| [test_guardian_composition.py](../../tests/test1/test_guardian_composition.py) | Missing/unreachable local child gates rejected before processing; MRO/system-check assertions |
| [test_guardian_parent_none.py](../../tests/test1/test_guardian_parent_none.py) | Legacy None-parent semantics, create state, FK/M2M, inherited policy annotations; migrate expectations deliberately |
| [test_guardian_policy.py](../../tests/test1/test_guardian_policy.py) | Global/object/group/superuser/inactive matrix, removed-field rejection, strict ViewSet helper, manage policy reporting |
| [test_guardian_content_types.py](../../tests/test1/test_guardian_content_types.py) | Guardian configured content types, proxy/polymorphic permissions, isolated permission/content-type caches |
| [test_guardian.py](../../tests/test1/test_guardian.py), [test_guardian_card.py](../../tests/test1/test_guardian_card.py) | Existing shipped Guardian request families and card behavior |
| [test_guardian_child_link_visibility.py](../../tests/test1/test_guardian_child_link_visibility.py) | Existing child-collection helper behavior; identify bounded migration dependencies without adding full parity |
| [test_cancel_permissions.py](../../tests/test1/test_cancel_permissions.py) | Parent/create access helpers used in cancel paths; local/ancestor policy dependencies |
| [test_action_enabled.py](../../tests/test1/test_action_enabled.py) | Permission and action-state separation, correct parent/child object input |
| [test_authorization_templates.py](../../tests/test1/test_authorization_templates.py) | Existing rendering contracts; preserve unrelated behavior, do not promise new traversal parity |
| [test_custom_form_view.py](../../tests/test1/test_custom_form_view.py) | Object/no-object custom forms and processing behavior |
| [test_resource_viewset.py](../../tests/test1/test_resource_viewset.py), [test_resource_views.py](../../tests/test1/test_resource_views.py) | Resource model/mixin boundaries, explicit permission mappings, and existing nested Resource-leaf scoping to preserve under D-39 |
| [test_guardian_delete.py](../../tests/test1/test_guardian_delete.py) | Guardian delete-related behavior that should not be accidentally rewritten |

[tests/test1/conftest.py](../../tests/test1/conftest.py) configures Django through `pytest_configure()`, with
in-memory default/shard SQLite databases, ModelBackend plus Guardian's ObjectPermissionBackend, and no
Guardian anonymous DB user. Test models live in [app/models.py](../../tests/test1/app/models.py): Author has a
UUID PK; Publisher/Book support a FK chain; BookNote extends that chain; Genre has an M2M relation to Publisher.
PublisherProxy and polymorphic models support content-type cases. Prefer these for focused fixtures rather
than creating a broad new test domain.

Dynamic authorization fixtures in `test_guardian_parent_none.py`, `test_authorization_matrix.py`, and
`test_guardian_content_types.py` create unique ViewSet names and temporary URL modules, restoring registry,
URL caches, vocabulary caches, and permission/content-type caches as applicable. Reuse that discipline; class
definition registers views immediately. A leaked registration can contaminate unrelated tests/system checks.

[tests/lib/helper/guardian.py](../../tests/lib/helper/guardian.py) contains `user_guardian_object_perm()`;
[tests/lib/helper/user.py](../../tests/lib/helper/user.py) contains `user_viewset_permission()` for model grants.
Model and object grants must be tested independently. Explicitly test retained child grants after parent
revocation to prove ancestor enforcement rather than accidentally relying on membership synchronization.

Suggested future verification commands, after implementation and environment setup; NOT run for this handoff:

```bash
pytest tests/test1/test_authorization_matrix.py tests/test1/test_fragment_authorization.py tests/test1/test_guardian_composition.py tests/test1/test_guardian_parent_none.py tests/test1/test_guardian_policy.py tests/test1/test_guardian_content_types.py tests/test1/test_cancel_permissions.py tests/test1/test_action_enabled.py -n 4
pytest tests -n auto
```

Use a bounded worker count when resources are shared. Small targeted debugging selections may run serially
with a reason. Add new cascade-specific tests to the focused command once their filename exists; no such test
file has been created. Existing legacy-policy fixtures may need explicit migration under the new default;
do not globally disable protection just to make them pass.

[noxfile.py](../../noxfile.py) defines Python 3.12/3.13/3.14/3.15 × Django 4.2/5.2/6.0, skipping Django 4.2 on
Python 3.14+. [pyproject.toml](../../pyproject.toml) currently declares Python >=3.12, Pydantic >=2.2.1, optional
Guardian >=2.4, and pytest-xdist among test dependencies. Core must remain importable without Guardian.
Use the repository's appropriate matrix for the implemented change; no environments were installed here.

Measure performance with fixtures that distinguish cold/warm permission vocabulary and request-local object
checks. Nearest-only must avoid higher-ancestor permission evaluation, not pretend relationship joins or
ancestor existence checks cost nothing. Keep state request-local and verify revocation on a fresh request.

### H. Upstream finding, downstream evidence, and confidentiality

The initiating demo finding is section 23 of
`../tabler-test/docs/crud_views_upstream_findings_roastery.md`. Its relevant source files are
`example/sales/views/addresses.py`, `views/customers.py`, `permissions.py`, `seed.py`, and
`tests/test_customers.py`, relative to that demo's `example/sales` directory where appropriate.

The demo uses a Guardian customer ViewSet, plain address ViewSet, and `CustomerGrantMixin.dispatch()` to check
the URL customer before core address permission checks. `can_on_customer()` accepts either a customer model
permission or an object grant. The account-manager group receives address model permissions. Read operations
require customer view; writes require customer change. That concrete mixin is unnecessary only after an
equivalent shared ancestor policy protects every relevant request. The app navigates through Sales → Customers
→ customer detail → Addresses. These files were inspected, not changed or tested.

The separately reviewed application uses per-container Member/Manager groups with real child object grants
and Guardian child views. Ordinary foreign-parent access differs from the demo; deeper access can still rely
on consistent memberships because only the immediate parent is checked. Reparenting, stale grants, and
policy-refresh concerns are separate from this feature. Use only the
[sanitized analysis](2026-11-07-entity-role-permission-pattern-analysis.md) for that evidence. Do not recover or
publish identifying names/paths from older conversation context, nor treat a source-level conditional concern
as a reproduced exploit. The deployed dependency version was not established in that review.

### I. Documentation and safe resumption boundaries

Likely documentation changes after implementation: [guardian.md](../../docs/reference/guardian.md),
[settings.md](../../docs/reference/settings.md), [custom_form_view.md](../../docs/reference/custom_form_view.md),
[action_enabled.md](../../docs/reference/action_enabled.md), and the relevant nested-ViewSet reference.
Search for old parent keys across docs/tests/templates before editing. A Breaking entry in
[CHANGELOG.md](../../CHANGELOG.md) also requires [migrating-1.0.md](../../docs/migrating-1.0.md).
D-49 specifically requires both documents to name the breaking nested custom action-entry requirement for
core and Guardian applications, in both cascade modes, with an exact-key declaration example and the
system-check/runtime configuration failure when an entry is missing. Explain the built-in/default and
top-level exceptions. Add these release-document changes with implementation; this design review only records
the requirement.

Preserve the local manage access policy when updating diagnostics; D-45 explicitly adds normal ancestry
checks to nested manage requests while retaining that independent local gate. Findings
24/25 remain outside scope. Do not revive retired integrated URL/navigation work; this feature's traversal
is for request authorization, not general destination resolution.

Before a future implementation begins, the plan must make these engineering details concrete: one reliable
entry point before protected processing; operation classification and explicit custom mappings; distinct
structural and nearest-protected parent resolution; anonymous denial behavior; import-safe checks versus
runtime key resolution; migration of all old-field consumers; and supported relation/database boundaries.
These are known work items, not excuses to restart the product discussion. If a solution becomes difficult
for the maintainer to explain and own, reduce complexity and revisit scope explicitly.
