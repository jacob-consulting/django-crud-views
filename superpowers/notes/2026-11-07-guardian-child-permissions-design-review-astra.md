# Ancestor authorization design review

Date: 2026-11-07.

Reviewed: [ancestor authorization design](2026-11-07-ancestor-authorization-design.md), including its decision
ledger and technical addendum, with the [discussion](2026-11-07-guardian-child-permissions-discussion.md) consulted
for intent. Source inspection and small runtime probes used checkout
`4b256bdbfd770b1b48d9318c384eeb35db06f97e`.

Original review text and source line references below describe the reviewed revision. Subsequent maintainer
decisions are recorded separately here; the original assessment and findings remain unchanged.

## Maintainer dispositions

| Finding | Status | Agreed resolution |
| --- | --- | --- |
| F-01 — ancestor queryset source and identity | **Accepted with revised loading contract, 2026-11-07** | D-51 uses each ancestor ViewSet's get_queryset(view=requested_child_view), preserves its filters, validates relationships, and reuses the resolved structural parent. No model-manager fallback or ancestor view dispatch. First-wave nested traversal supports default only for ORM ancestry, ORM child data, and relevant authorization records; nondefault queryset/routing selections are configuration errors, never stripped or redirected. Explicit using("default") is valid; top-level behavior is unchanged. |
| F-02 — URL-path mutation boundary | **Accepted as a scope clarification, 2026-11-07** | D-52 limits ancestor authorization to the declared URL path. Additional protection required for shared-object writes, parent changes, or effects outside that path belongs to the endpoint/application. Preserve save/delete semantics; full cascade does not enumerate other parents, pin an editable parent FK, authorize a destination, or turn deletion into unlinking. Document shared-M2M and editable-FK examples. |
| F-03 — cycle-validation timing | **Accepted, 2026-11-07** | D-53 requires bounded, actionable cycle/missing-reference errors at or before URL construction can enter an unbounded walk, with system-check/request safeguards retained. Use registration metadata without database queries, preserve valid forward references, and reuse a small structural validation mechanism across relevant ancestry walks. |

F-01's discussion initially proposed retaining model-default-manager lookup. The maintainer pointed out that
developers expect ViewSet queryset restrictions to govern descendant access, and approved using the ancestor
ViewSet queryset with the actual requested endpoint as context. Shared parent identity is retained across
authorization, create attachment, and parent-based state checks. The maintainer also approved default-only
database support for the first wave, with explicit errors for nondefault selection rather than silently
ignoring using(...) or routing. The design's operative contract, migration/validation tables, acceptance
criteria, and technical addendum were updated. The maintainer subsequently requested a documentation commit
before discussing F-02. F-02/F-03 resolutions follow below; all three findings now have approved dispositions.
Planning and implementation remain deferred.

F-02's approved resolution makes the existing URL-path boundary explicit, including when the same child is
shared with another parent or a form permits changing its parent FK. Applications own any additional
authorization or constraints required by their domain; no automatic container-isolation guarantee is added.
The design's scope, request continuation, acceptance examples, and technical addendum were updated while
preserving standard save/delete behavior. The maintainer requested a documentation commit and discussion of
F-03. Original review text remains preserved below; implementation remains deferred.

F-03's approved resolution ensures the promised configuration error can be reached during URLconf import,
before URL generation hangs in a parent cycle. Valid forward references remain supported during registration;
the chain must resolve when it is needed. Validation requires no database queries and can use a small shared
structural walk. The maintainer discussed the bounded implementation cost, then approved the clarification
and requested a documentation commit. The design's validation/request contracts, acceptance criteria, and
technical addendum were updated. All three Astra findings are resolved at the design-document level under
D-51–D-53, ready for design-v2 consolidation. Original findings remain unchanged below; planning and
implementation remain deferred.

## Assessment

The central design is coherent. Explicit ancestor providers, operation requirements owned by the requested
ViewSet, independent child gates, and one traversal for both cascade depths address the motivating problem.
The distinction between structural parent and nearest protected ancestor is particularly important and is
handled consistently. I would preserve these decisions and the approved public configuration API.

I recommend three targeted amendments before implementation: specify the source of ancestor objects and its
scope guarantees; explicitly bound authorization of mutations to the declared URL path; and require cycle
validation before URL construction can enter an unbounded walk. The first is an observable-behavior gap, the
second is a security-boundary documentation gap, and the third is a validation-lifecycle gap. All are P2
(important to resolve, without evidence of a critical vulnerability in a new implementation).

This review does not establish an exploit in the proposed mechanism: it has not been implemented. It separates
observed current behavior from consequences inferred for a future implementation. No implementation plan,
production changes, staging, or commit are part of this review.

## Findings

### F-01 — P2: Define which queryset supplies ancestor objects and keep their identity consistent

**Design locations:** request behavior, lines 588–595; technical addendum C, lines 936–940; database boundary,
lines 1106–1109. Related decisions: D-10, D-29, D-32.

“Resolve ancestors … using declared URL argument names and relationships” leaves an observable choice:
whether resolution uses the model's default manager, the ancestor ViewSet's `get_queryset()`, or an existing
parent-loading override. These are not interchangeable in this repository.

The current [ViewSet.get_queryset()](../../src/crud_views/lib/viewset/__init__.py) at line 281 is overridable and
uses `model.objects`. The existing
[configured-content-type test](../../tests/test1/test_guardian_content_types.py) at line 124 demonstrates an
application ViewSet override supplying both `.using(...)` and a row filter. In contrast,
[CrudView.cv_get_parent_object()](../../src/crud_views/lib/view/base.py) at line 1028 passes the model directly
to `get_object_or_404()`, bypassing that ViewSet override. The old Guardian parent gate does the latter too.

**Observed:** an in-memory probe created a parent excluded by a ViewSet queryset filter. The queryset did not
return it, but `cv_get_parent_object()` did. This establishes the semantic difference; it does not establish
that the design intends ancestor endpoint filters to be security gates.

**Consequence:** two plausible implementations can disagree about whether a filtered-out ancestor exists.
Likewise, an explicit database choice in a ViewSet override is different from model-router selection. Merely
requiring “configured DB routing” does not settle whether that override participates. An implementation could
also authorize an object using one resolution path and later obtain the structural parent through another:
`CreateViewParentMixin.cv_form_valid()` calls `cv_get_parent_object()` again when attaching the child. Database,
model identity, and PK must agree between authorization and consumption.

The prohibition on dispatching ancestor views does not resolve this: a ViewSet queryset is not a view dispatch.
Conversely, it would be unjustified to infer that every ancestor's endpoint-specific filters must now apply.

**Recommended amendment:** state one ancestor-loading contract, including the manager/queryset used, whether
ViewSet and view-level lookup overrides participate, and the supported database topology. If the bounded
choice is model-manager resolution, explicitly say that ancestor ViewSet/queryset filters are not inherited
authorization constraints. Require supported structural-parent consumers to use the same resolved identity;
document incompatible custom lookup overrides rather than silently mixing them. This does not require a new
public loader framework or dispatching ancestor views.

**Acceptance evidence:** cover a parent excluded by an ancestor ViewSet filter, a model with a filtering default
manager, and a supported nondefault database route. Assert the chosen behavior and that the parent authorized
is the one supplied to create attachment and state checks. If multiple aliases are supported, use overlapping
PKs so a wrong-database lookup cannot accidentally pass. The existing shard test at line 397 of
`test_guardian_content_types.py` explicitly tests a superuser queryset fast path, not ordinary cross-database
Guardian grants; it is not sufficient evidence for the latter.

### F-02 — P2: Make the URL-path-only mutation boundary explicit, especially for M2M

**Design locations:** scope, lines 215–231; operation mapping, lines 499–510; request continuation, line 595;
acceptance evidence, lines 825–838. Related decisions: D-05, D-10, D-13, D-29.

The approved mechanism checks the declared URL ancestry. That is a well-defined and useful boundary, but it
does not establish that all data affected by a write belongs exclusively to that ancestry. The affirmative
M2M support statement needs to explain this distinction.

Consider a `Genre` linked to publishers A and B, using the existing
[Genre model](../../tests/test1/app/models.py) at line 55. A user has change permission on A and none on B. A
nested update through A satisfies the proposed ancestor gate. If the child-local gate also passes, the
[standard update handler](../../src/crud_views/lib/views/update.py) at line 30 saves the shared Genre itself.
B therefore sees the changed name too. Checking every ancestor in the URL cannot discover B, because B is
another parent, not an ancestor on that path. This remains true with full cascading enabled.

**Observed:** an in-memory probe linked one Genre to two publishers and invoked the existing update handler
with a valid name form. Reading the Genre through the second publisher returned the changed name. The probe
verified shared-row mutation, not authorization by the unimplemented traversal.

The corresponding FK boundary is also relevant: an update form that exposes its parent FK can move the child
after the original URL ancestry has passed. `UpdateView.cv_form_valid()` saves the form without pinning that
FK or authorizing its new value. The design excludes permission repair after moves, but that is separate from
explaining who must authorize the move itself. Custom actions can similarly affect records outside the URL.

**Consequence:** “M2M supported” and “full relationship validation” can be mistaken for a guarantee of isolation
between containers. The actual design authorizes the current path and leaves the effects of the operation to
the endpoint/application. This is especially important because deliberately absent child-local gates are
supported. A child grant, when present, is also not automatically a permission on every related parent.

**Recommended amendment:** retain the approved traversal and say explicitly that it authorizes the URL path,
not every parent or object affected by a mutation. Document that shared-child writes, changes to parent
relationships, and actions with effects outside that path need application-owned constraints or authorization.
For an application requiring isolated container ownership, an unrestricted shared-child editor is not made
safe merely by enabling cascade. Do not silently add all-membership traversal, change deletion into unlinking,
or introduce a generic mutation-policy engine. Those would be new scope and behavior.

**Acceptance evidence:** include a two-parent shared-child example and an editable-parent-FK example in the
documented boundary tests/examples. Make the expected behavior explicit. If stronger isolation is intended,
that is a genuine additional requirement to settle, not an implementation detail of relationship lookup.

### F-03 — P2: Cycle rejection must be reachable before URL generation walks the chain

**Design locations:** C-02 validation, lines 386–388; request behavior, lines 582–586; addendum B,
lines 925–926. Related decisions: D-32, D-36.

The design correctly requires cycle detection, Django system-check errors, and runtime guards. It also notes
that existing walkers are not cycle-safe. The missing acceptance condition is that URL construction itself
must terminate with a configuration error when the registry contains a cycle.

[ViewSet.urlpatterns](../../src/crud_views/lib/viewset/__init__.py) at line 404 calls `get_path_parent()` before
creating a request callable. `get_path_parent()` at line 363 follows `parent.viewset.parent` in an unbounded
loop. A URLconf can evaluate these properties during import, before a request guard or a later system check
can report the error. Other existing parent helpers also walk without cycle detection.

**Observed:** a probe constructed two ViewSets whose parent references pointed to each other and accessed
`one.urlpatterns`. A 100 ms alarm interrupted the parent walk; no configuration error was raised. Source
inspection confirms that the loop has no termination condition for this graph. The alarm prevented an
unbounded process during review.

**Consequence:** implementing validation only in the new request traversal or a system-check function leaves
a startup/import hang instead of the promised actionable configuration error. This matters independently of
permissions and occurs before database access.

**Recommended amendment:** require safe ancestry validation at or before URL construction, as well as in the
stated check/request paths. Reuse a small structural walk or shared validation result where appropriate;
there is no need for a second URL-routing system. Preserve registration-order flexibility: a valid forward
reference should not fail simply because the second ViewSet has not yet been constructed.

**Acceptance evidence:** exercise self-cycles, two-node cycles, and missing references through actual
`urlpatterns`/URLconf construction as well as direct checks. They must produce bounded, actionable failures
without permission-table queries. Also verify a valid forward reference once registration is complete.

## Decisions that hold up under review

- **The policy split is consistent.** An ancestor owns its provider and fallback; the requested ViewSet owns
  traversal depth and operation requirements. `provider="none"` does not disable the owner's own traversal.
- **Nearest-protected selection is sound.** Selecting from declarations, passing through none levels, and
  retaining full relationship validation avoids treating failed permission checks as opportunities to fall back.
- **Failure ordering is adequately specified.** B-01/B-03 distinguish configuration errors, actor denial,
  reached relationship failures, and permission denial. They do not require probing deeper objects after denial.
- **Guardian migration is deliberately bounded.** Removing the old gate while preserving child checks, actor
  handling, create state, and the no-child-add nested-create behavior is consistent with the approved changes.
  B-05 also addresses consumers that would otherwise retain references to removed fields.
- **Visibility mismatch is an accepted limit.** A shown link leading to a newly denied request is not a finding
  against this design. Expanding every helper into full ancestry traversal would violate the agreed scope.
- **The configuration types remain data.** Strict pair validation, explicit inheritance, and runtime resolution
  of database-backed permission keys give a maintainable boundary without a policy execution framework.

## Implementation review points, not additional design findings

The following risks are already constrained sufficiently by the design; they need evidence during
implementation rather than another product discussion:

1. **Prove the entry point precedes local processing.** Core permission-required views can run
   `has_permission()` and load the child before `CrudView.dispatch()`. Guardian parent dispatch and ManageView
   have different MROs. Trace the shipped compositions and use spies to prove a denied ancestor prevents child
   lookup, state hooks, fragment choices, and writes. Merely adding code to `CrudView.dispatch()` is insufficient,
   as the design already recognizes.
2. **Classify package families narrowly.** `CustomFormView` inherits Django's generic DetailView but requires an
   explicit action declaration. A broad check against Django's DetailView would misclassify it. Built-in ordered
   actions inherit generic ActionView but are explicit writes. Retain the finite approved table. The exported
   `RedirectChildView` is not named there; under the existing unknown-operation rule it needs an explicit mapping
   when nested unless a later decision deliberately adds it to the built-ins.
3. **Prove fallback independence in both directions.** An ancestor accepting global grants must not relax a
   strict child object gate. A child accepting global grants must not relax a strict ancestor. Include core/plain
   children beneath Guardian ancestors, not just all-Guardian compositions.
4. **Keep selected and unselected vocabulary separate.** A missing key on a selected ancestor must error; a
   higher ancestor omitted by nearest-only mode must not trigger a permission-map lookup. Relationship checks
   still apply to that higher ancestor.
5. **Review maintainability separately from test count.** The implementation should have an identifiable request
   entry point and a short top-down flow. Avoid duplicating policy resolution in request gates, create helpers,
   cancel helpers, and diagnostics. The two roles within `AncestorPolicy` need clear developer documentation,
   but do not justify another abstraction layer.

Concurrency between authorization and later writes is not solved by request-local caching or by the existing
write transaction. I do not recommend adding locking to this feature without a demonstrated requirement.
Document a request-time authorization guarantee, not serializable protection against concurrent reparenting
or permission changes. The specified next-request revocation guarantee remains useful and testable.

## Evidence and limits

I inspected the design and relevant discussion, core registry/URL/queryset paths, permission and parent
helpers, create/update/delete/action/form/manage views, Guardian provider and mixin code, and relevant test
fixtures. Three small probes ran using the existing `.venv` and the test configuration's in-memory SQLite
database. They used serial execution because they were isolated behavior probes, not a broad test run.

The probe output was:

```text
Filtered ancestor queryset sees hidden parent: False
Current structural-parent loader sees hidden parent: True
Update through one parent changes other parent row: Shared after
Cyclic ViewSet URL generation: timed out in existing parent walk
```

No full test suite, framework matrix, or performance benchmark was run. The proposed API cannot be tested
yet. The probes wrote only to the process-local in-memory database and did not change source or test files.
Existing unrelated working-tree changes were preserved. The findings above are recommendations for amending
the design, not edits to the approved ledger or authorization to begin implementation.
