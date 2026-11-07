# Entity role groups and nested authorization

Date: 2026-11-07. Status: read-only analysis for an open design discussion.

This note deliberately uses generic names and omits the reviewed project's identity, source-root paths,
business terminology, and data. No implementation is proposed or approved. Do not stage or commit this note
unless subsequently requested.

## Main conclusion

**The representative content routes do not show the same authorization gap as the plain child ViewSet in
the demo.** Both the immediate parent and the child content use Guardian object checks. Global child model
permissions alone do not satisfy these checks under the inspected configuration.

**That does not establish authorization of every ancestor in a nested URL.** Deeper views check the immediate
parent and the child. Authorization above that parent relies on consistent role memberships. Moves or
inconsistent memberships can break that assumption.

The distinction matters: the demo lacks a parent authorization gate on its plain child views; this pattern has
that gate, but does not recursively authorize the entire ancestor chain.

## Scope and evidence limits

- A delegated source review examined the role/group helpers, model permission declarations, lifecycle signals,
  representative nested content and membership views, forms, administration configuration, activity access,
  and existing authorization tests.
- The reviewed application declares a framework version range of `>=0.25.0,<0.29.0`. The framework's local
  `v0.25.0` and `v0.28.0` source tags were inspected. No local environment or lockfile established the deployed
  version; the review does not certify every release in that range.
- Tests were read, not executed. No dependencies were installed, application data accessed, or customer files
  changed. No live HTTP exploit was reproduced.
- Conclusions apply to the inspected paths. Conditional weaknesses below are not claims that unauthorized
  access has occurred in deployment.

## The designed pattern

Use **outer container → inner container → content** as the generic relationship.

1. Each container owns Member and Manager Django groups. Group names include the entity type and its UUID.
2. Membership records synchronize a user's participation in those groups according to role flags.
3. Models declare which object permissions each role receives.
4. Content creation assigns permissions on that specific content object to its owning container's groups.
   Content reuses those groups; it does not need its own pair of groups.
5. Inner containers have independent groups and membership records. Open inner containers receive memberships
   derived from outer memberships; private inner containers require explicit membership.
6. Deleting an outer membership removes its group participation and deletes subordinate memberships. Their
   deletion removes subordinate group participation too.

The result stores child object grants ahead of requests. It does not infer arbitrary permission inheritance
from the URL at request time. The group's membership supplies the users; the group's object grants supply the
permitted operations and objects.

## What happens when someone changes the URL

| Case | Reviewed behavior | Evidence and limits |
| --- | --- | --- |
| Another immediate parent and its own child, with no relevant grants/group membership | Parent Guardian gate denies, normally 403; the child has its own object gate too | Source-supported; matching tests read |
| Allowed parent paired with another parent's child | Relationship-scoped queryset excludes that child; object lookup returns 404 | Source-supported; matching tests read |
| User holds only global child model permission | Strict Guardian child checks still require object access | Inspected framework defaults; no application global-fallback override found |
| Inner membership remains while outer ancestor access is absent | Deeper content view checks the inner container and content, without independently authorizing the outer ancestor | Framework structure confirmed; depends on inconsistent or moved membership state |
| Create URL names a wrong outer ancestor but an allowed immediate parent | Immediate parent is resolved and used for attachment; no explicit full-chain validation found on the representative create path | Source-level concern; full HTTP behavior not reproduced |

For object reads and updates, relationship validation traverses the configured ancestor chain. Permission
validation does not traverse the entire chain. Creation also deserves separate examination because there is
no existing child-object lookup to supply that relationship validation.

## Strengths

- **Child access is actually scoped.** Membership in one container does not grant ordinary users permissions
  on another container's content.
- **Revocation is economical.** Removing a user from a role group withdraws the access supplied by that group
  across its content, without rewriting every child's permission rows. Other independent grants can still
  supply access, as expected.
- **Policy is explicit per model.** Content and administrative membership operations can grant different
  powers to the same role. Member permission to change/delete content is a deliberate policy in the inspected
  declarations, not by itself a security defect.
- **Normal lifecycle handling exists.** Creation assigns object grants; membership changes update role groups;
  deletion withdraws memberships, including subordinate memberships on outer-membership deletion.
- **Existing tests target the boundary.** Tests cover outsiders, private-container isolation, revocation,
  foreign-child requests, and wrong-parent requests. A registry coverage test requires content ViewSets to
  appear in the access matrix. These tests were not run in this review.
- **Ordinary forms restrict reassignment.** Content forms do not expose the parent FK, and existing membership
  identity/container fields are read-only in the relevant administration form.

## Weaknesses and limits

### 1. Ancestor authorization depends on membership consistency

The Guardian parent gate checks the immediate parent, not all ancestors. Consider moving an inner container
from outer container A to outer container B while keeping its existing inner memberships. The reviewed
administration registration appears to allow the outer FK to change, and no corresponding membership
reconciliation was found for that move.

A previous inner member may then retain permission on the inner container and content without permission on B.
The inner container's own view checks B and denies access. A deeper content view checks the inner container
and may allow access through a relationship-valid URL under B.

This is a concrete conditional concern supported by the source structure, not a reproduced exploit. It
conflicts with the proposed expectation that every URL ancestor must be authorized. Whether retained inner
access after a move is acceptable remains a product-policy question.

### 2. Grant synchronization does not implement arbitrary reparenting

Content grants are assigned on creation. Moving existing content to another container does not automatically
withdraw the previous container's grants and supply the new container's grants.

Even explicitly invoking the synchronizer cleans grants only for groups found through the object's current
ownership mapping. Old-owner groups can fall outside that mapping and retain stale grants. The normal
immediate-parent gate limits their usefulness on nested routes, so this alone does not prove a bypass there.
Other object-permission consumers can still observe stale grants, and new owners can encounter incorrect
denials. Ordinary frontend forms avoid parent edits; content administration registrations appear to allow them.

### 3. Selected lifecycle operations maintain the invariant

Deleting an outer membership cascades the necessary membership removal. Changing role flags, changing
membership identity programmatically, manually editing Django groups, or using bulk operations may not perform
the same reconciliation. These operations need explicit supported semantics; an invariant maintained by normal
forms and save/delete signals is not automatically maintained by every administrative or import path.

### 4. Membership-creation authorization is spread across layers

Membership-create views use an access helper to require Manager status for button visibility. That helper is
not the request-dispatch gate in the inspected framework tags; the generic parent gate otherwise checks
parent view permission by default.

The current bound user-candidate lookup independently requires Manager status and raises PermissionDenied.
Consequently, this review does **not** establish that an ordinary Member can create memberships or promote
someone. The concern is maintainability: a security requirement depends partly on a form-field lookup outside
the view gate. The field's dependency was not installed locally, so full request enforcement was not verified.

### 5. Stored grants require maintenance when policy changes

Changing a role's permission declarations does not automatically refresh grants on existing content.
Creation-time assignment and explicit synchronization determine stored permissions. There are two groups per
container and several permission records per child. This is understandable at bounded scale, but the supported
policy-refresh, repair, and reassignment procedures need to be clear.

## Implications for the ongoing discussion

The role-group design already solves the ordinary cross-container problem for the reviewed child content
routes without the demo's custom customer-checking mixin. Its remaining concern is deeper nesting and lifecycle
consistency, rather than global child permissions alone.

At the time of this review, the maintainer's question remained open: **should editing a child require permission
to view its parent, or permission to change that parent?** Subsequently, the maintainer chose **customer change**
for the address scenario, because addresses are part of customer configuration, while explicitly allowing that
other relationships need different rules. Whether child permission remains an additional gate is still open.
Independent authorization of every
ancestor, relationship validation at creation, and movement of existing containers/content are also separate
policy questions; no implementation scope has been agreed.

Related discussion: [Guardian child permissions](2026-11-07-guardian-child-permissions-discussion.md).
