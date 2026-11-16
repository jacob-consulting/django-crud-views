# Bulk actions

**Date:** 2026-11-16
**Issue:** [#378 — Bulk actions](https://github.com/jacob-consulting/django-crud-views/issues/378).
**Status:** approved discussion decisions and mockup flow, with separately identified implementation proposals
for GSD planning. This document is not approval to implement those proposals.
**Deliverable:** a GitHub enhancement issue containing this design and its `gsd-handover`. No implementation,
phase creation, worktree creation or roadmap scheduling is authorized by filing the issue.
**Baseline inspected:** `de13d1ae` on `main`.

## Problem / motivation

Deleting records individually is repetitive. Users should select records in a table or card list, review the
selection, and delete them together. The experience is inspired by Django admin actions, while preserving
django-crud-views' permissions, parent scoping and deletion protection.

Delete is the first built-in action. The public API must already accommodate developer-defined bulk actions,
so adding another action does not require redesigning selection or changing the initial API. Bulk creation
is not planned.

## Proposed solution

Add an explicit bulk-action list to list/card views. An empty list enables nothing. Developers opt into bulk
delete by adding it to that list; a registered single-record delete view alone does not enable bulk delete.

Share selection, confirmation and a selection-wide pre-check through a small bulk-action API. The built-in
delete action uses the registered delete view for supported permissions and per-record deletion rules.
One failed record blocks the entire operation. Execute supported database writes in one transaction.

The feature includes documentation and a separate example app with several working demonstrations.

## Alternatives considered

1. **Registered delete view as bulk delete's policy source — selected.** Keeps deletion permission and
   protection in one place. The single-record view need not appear in row actions, but its endpoint must
   exist. Bulk integration needs a documented supported-hook contract because not every HTTP/form override
   can be meaningfully reused for a selection.
2. **Independent bulk-delete policy — not selected.** Allows bulk-only deletion without a single-record
   endpoint, but duplicates permissions/business rules or requires a new shared public policy abstraction.
   That increases the risk of divergence and the developer's maintenance burden.

The general bulk-action API remains independent of this delete-specific dependency. A custom action does
not need a matching single-record view. Replaying the single-record HTTP handler per selected object is
not the chosen integration mechanism.

## gsd-handover

Carry the approved decisions below into planning without reopening them absent a concrete conflict.
Keep the proposals in the following section distinct from decisions explicitly made by the maintainer.
The prose and acceptance criteria are part of the handover, not just this decision index.

### D-01 — Scope and extensibility

Deliver selection and a minimal developer-facing bulk-action API, with bulk delete as the first built-in
action. Include a whole-selection pre-check and execution extension points. Do not build a deletion-only
public API that must be replaced to add another action. Do not add bulk creation, a general job system,
background processing, or several additional built-in actions.

### D-02 — Explicit activation

Bulk actions have a separate list on each source list/card view. Do not reuse or infer activation from
`cv_list_actions`, `cv_card_actions`, context actions, or registered delete views. Adding bulk delete to
this list is the developer's opt-in. An empty list produces no selection controls or bulk toolbar.
Disabled views must incur no selection-related queries or state management.

### D-03 — Registered delete view

Built-in bulk delete requires a registered single-record delete view in the same ViewSet. Use its supported
permission, applicability and protection behavior; do not create a second independently configured delete
policy. Registration does not require displaying the single-record delete action in rows/cards.

Permission checks and business protection are distinct: list visibility alone never grants deletion.
Per-record permission denial, a disabled delete action, custom delete-protection errors, and native database
protection must each block the batch. Add a separate whole-selection pre-check for aggregate business rules.
The pre-check is read-only and returns explanatory errors rather than silently dropping records.

### D-04 — All-or-nothing deletion

If any selected record cannot be deleted, block the entire operation and explain why. Do not delete an
eligible subset, skip failed records, or offer a partial-success mode. Check every selected record before
the first write and recheck when confirmation is submitted. A later database failure must roll back all
earlier database writes in the operation. Report success only after the transaction commits.

Do not confuse rollback of database work with reversal of external effects; email, files and remote APIs
cannot be made transactional by a database transaction. The documented extension contract must keep
irreversible side effects outside pre-checks and place post-success effects after commit where appropriate.

### D-05 — Supported data sources

Built-in bulk delete initially supports Django models, including nested and Guardian-protected views.
Non-ORM Resources, such as S3 objects, are deferred: their delete hooks do not provide database rollback.
Preserve parent authorization, parent-scoped lookup, Guardian object grants and configured global-permission
fallback. A user may see a row without being able to delete it.

### D-06 — Selection controls

Support individual row/card checkboxes and a checkbox for selecting/deselecting the current page.
Also support **Select all** for an unfiltered result and **Select all filtered** when filters are active,
including records beyond the current page. These operate within the source view's authorized, parent-scoped
result set. Never let the unfiltered control escape the current filters or view restrictions.

Show the number selected across pages. Manual selections persist when paging and are restored when the
user returns to a page. Applying or resetting filters clears the selection. Include a clear-selection
control. These behaviors were demonstrated in the approved mockup.

### D-07 — Independent controls for select-all and maximum size

The maintainer approved the following separation; names were presented as provisional:

| Configuration | Meaning |
| --- | --- |
| `cv_bulk_actions = []` | No bulk actions enabled on the source view |
| `cv_bulk_select_all = False` | Manual and current-page selection remain; no across-results Select all / filtered |
| `cv_bulk_max_items = 100` | At most 100 selected records per operation, however they were selected |
| `cv_bulk_max_items = None` | No configured item-count limit |

Both selection settings have global defaults and explicit per-list/card overrides. `None` is a deliberate
unlimited override, not inheritance; omitted values inherit. Numeric limits are positive integers.
The final names and default values are proposals below; the semantics above are settled.

Enforce the maximum on the server as well as in the UI. When the result exceeds the limit, explain how to
narrow the filters or select fewer records. Never silently choose the first N matches. The limit counts
selected roots; cascade-preview limits and numbers of related records are separate concepts.

**Superseded idea:** earlier discussion used `None` to disable across-results selection. The separate boolean
and maximum above replace that meaning. Do not carry the earlier interpretation into implementation.

### D-08 — Fixed confirmation selection

Prepare confirmation for explicit, fixed record identities. Newly matching records must not become part
of the deletion after review. Resolve current data and permissions again at execution. If a selected record
has disappeared or become ineligible, reject the whole operation with an explanation; do not shrink the
selection silently.

The server must validate the selection and its source context, including action availability, parent scope,
filters, limits and permissions. Client-provided IDs and cached UI state are never authorization evidence.

### D-09 — Approved presentation and flow

The maintainer approved the interactive table/card mockup served on port 9000 through the maintainer's
Cloudflare domain. A durable, standalone local copy is saved at
`superpowers/specs/2026-11-16-bulk-actions-mockup.html`; runtime session keys do not belong in the issue or
repository. The behavior below is self-contained so the issue does not depend on a live preview server.

- Put a selected-count indicator, bulk-action picker and Continue button above the records.
- Use a selection message to distinguish the current page from all matching records.
- Continue to a dedicated confirmation page showing the fixed selection and relevant deletion effects.
- Require explicit confirmation before enabling the final delete button.
- On a blocked selection, show an explanation and a return-to-selection action; no executable delete button.
- Cancel/back preserves selection. A successful operation returns to the source list/card and clears it.
- Use one success result for the batch. Show a generic explanation when detailed reasons would reveal data
  the user is not permitted to inspect.

The mockup's prototype-only control panel, fictional data, inline scripts/styles and simulated deletion
are not production requirements. Follow the existing theme/class registry, template extension, translation,
accessibility and external-asset/CSP conventions in the actual feature. Modal confirmation is not needed
for this first implementation.

### D-10 — Documentation and a separate example app

Documentation and working examples are deliverables of this issue. Create a dedicated `bulk_actions` app
under `examples/bootstrap5/`, rather than adding one isolated demonstration to the existing library app.
Include multiple examples, seed data, routes and the existing feature-navigation/documentation integration.

Cover activation, selection, both configuration settings, the public custom-action/pre-check contract,
registered-delete-view reuse, permissions, confirmation, transactional guarantees and explicit limitations.
Cross-link the reference documentation and example pages. Include a custom action example to demonstrate
that the general API works without requiring a corresponding single-record action view.

### D-11 — Maintainability and handoff

Keep this opt-in and understandable by the project developer. Preserve the proven single-record deletion
path and current list/card behavior. Reuse shared permission/deletion primitives where they fit; do not
introduce ambient state, a generic HTTP-view replay engine or a broad policy rewrite.

The requested outcome is a GitHub issue with all decisions and context, ready for later GSD planning.
Filing the issue does not itself implement the feature or schedule a phase.

## Proposed defaults and bounded implementation contract

These are author recommendations for review, not additional claims of maintainer approval.

### A-01 — Configuration and public API shape

Keep the provisional `cv_bulk_actions`, `cv_bulk_select_all` and `cv_bulk_max_items` names. Propose global
`CRUD_VIEWS_BULK_SELECT_ALL = True` and `CRUD_VIEWS_BULK_MAX_ITEMS = 100`. Bulk actions still default to an
empty per-view list. Thus select-all appears only on explicitly enabled views. Reject invalid configuration
with system checks; distinguish an omitted maximum from explicit `None`.

Prefer a small action class/descriptor carrying a stable action key, label, permission/applicability
behavior, a selection-wide check and execution. Expose request/source-view context and resolved selected
objects to the hooks. Authorization, validation and execution must be distinct stages. The bulk framework
owns scope validation and the atomic write boundary; actions cannot make client IDs authoritative.

Exact class names, list-entry syntax, import paths, hook signatures, error types and route names remain
builder choices. Document and demonstrate the initial public contract. The example custom action should
exercise that contract without introducing another built-in library action.

### A-02 — Selection storage and navigation

Use tab-scoped browser storage for explicit selected IDs; persist pagination, ordering and reloads.
Scope state to actor/session, source view and parent coordinates plus effective filters. Table and card
views have separate selections. Clear selection when filters change, on successful completion, or when
the source context changes. Cancel/back preserves it. No persistent cross-tab basket or cross-device state.

Resolve Select all / filtered on the server, applying the source view's actual queryset/filter logic and
the maximum before returning selected identities. Use the same explicit-ID selection representation for
manual and across-results selection. Selecting all then unchecking a row removes that ID. Do not maintain
a live query that keeps adding matches. Preserve supported PK encodings without converting UUIDs/strings
to JavaScript numbers.

Protect the confirmation's identities and source/action context against modification between review and
execution. The builder may choose a signed payload or an expiring server-side snapshot based on payload
size and existing infrastructure. Do not add mutable shared session state on every checkbox click.
The confirmation is an identity snapshot, not a database lock or a promise that rows cannot change.

### A-03 — Delete reuse and customization boundary

Support the package's standard core, nested, Guardian and polymorphic delete paths. For per-record checks,
provide the real request, parent coordinates and `self.object` to supported delete-view hooks. Reuse
`cv_check_delete_protection()`, applicability gates and existing deletion inspection/visibility behavior.
Use actual request authorization semantics, including custom restrictions, rather than only checking
the template button helper `cv_has_access()`.

Do not pretend arbitrary downstream HTTP handlers, form fields/`clean()`, lifecycle overrides or model
delete side effects automatically become a bulk operation. The built-in integration must explicitly
support or reject them before writes; it must never silently bypass a custom check or write hook.
Propose a documented compatibility check and an explicit custom bulk-action adapter for unsupported
customizations. Package-standard messaging is aggregated instead of issuing one message per object.

The precise supported/rejected customization matrix is a planning deliverable and must be demonstrated
against core and Guardian examples. Do not rewrite single-record behavior to make the matrix universal.

### A-04 — Database and deletion boundaries

Require all selected roots and supported writes to use one database alias. Reject cross-database batches
before writes and preserve existing nested/Guardian database restrictions. The bulk operation's outer
transaction is mandatory even when a source view has opted out of single-record atomicity. Tests must
prove rollback if a later deletion fails. Unexpected programming/hook errors propagate after rollback;
do not label every exception as deletion protection or report failed commit callbacks as a rolled-back
deletion. Do not send successful messages or callbacks for rolled-back objects.

Preserve supported model deletion semantics and signals; a raw `QuerySet.delete()` is not a sufficient
substitute if it bypasses a model override or the package's deletion execution safeguards. Do not implement
new SQL deletion logic. Conservative refusal is acceptable for unsupported customization/relationship cases
when documented and detected before mutation.

Do not promise arbitrary cross-row concurrency locking or external rollback. At confirmation submission,
re-resolve and check the complete fixed selection inside the write boundary; retain native database
protection as the write-time backstop. Preview inspection is descriptive, never reused as write instructions.
Overlapping cascades must not inflate unique effect counts or produce success for an unintended subset;
planning must explicitly address overlapping selected roots without sacrificing maintained delete behavior.

### A-05 — Example scenarios and documentation locations

Propose `docs/reference/bulk_actions.md`, linked from list, card, delete, Guardian and request-lifecycle
documentation and the MkDocs navigation. Update the settings reference, changelog and any affected API
reference. If implementation introduces a Breaking entry before 1.0, update `docs/migrating-1.0.md` too.

The separate example app should have discoverable demonstrations of:

1. A paginated, filtered table with manual/page/all-filtered selection and successful bulk delete.
2. A card view with selection, an explicit per-view maximum and a manual-only/select-all-disabled variant.
3. Protected records and an aggregate pre-check that vetoes the entire selection, with visible explanations.
4. Nested scope and Guardian users with different view/delete grants, proving a denied member blocks all.
5. A small custom bulk action, such as archiving selected drafts, using the same public selection/check/
   execution API without a single-record counterpart.

Use enough seeded records to span multiple pages and exceed a demonstrated limit. Follow the existing
example-app seed/reset and feature registry conventions; make destructive examples repeatable. Show
configuration/source pointers and reciprocal documentation links. Test app registration, seeding, and the
demonstrated behaviors; examples must use the public API, not private shortcuts.

### A-06 — HTTP, visibility and recovery

Selection preparation/confirmation must never delete records. Final mutation is a CSRF-protected POST;
GET does not execute an action. Only actions actually enabled on the source view are dispatchable. Reject
empty, malformed or out-of-scope selections and revalidate the maximum at execution. Deduplicate IDs before
counting/checking, without dropping unknown or inaccessible identities.

Use existing source navigation/filter conventions for cancellation and successful return. Expired or
invalid confirmation state requires fresh review, never fallback to a newly evaluated all-results query.
Re-check root visibility before rendering confirmation and related-object visibility before rendering
labels. Browser-persisted names/counts are not permission evidence. Additional hardening and token lifetime
details are builder choices within these requirements, not a new generalized session subsystem.

## Acceptance criteria

1. Empty bulk-action lists leave tables/cards unchanged and add no selection-related queries. Bulk delete
   appears only after explicit addition and requires its registered delete view.
2. Table and card row selection, page selection, cross-page counts, clear selection and filter-reset behavior
   match D-06/D-09. Returning to a selected page restores its checkboxes.
3. Select all and Select all filtered include matching rows beyond the visible page while preserving source
   restrictions and parent scope. A later matching row never enters the confirmed selection.
4. Global defaults and per-view overrides work independently. Disabling select-all retains manual/page
   selection. Positive maximums apply to every selection method; explicit `None` removes the configured cap.
   Over-limit results are rejected/explained, never silently truncated.
5. Core permissions, Guardian object permissions/global fallback, parent authorization, action applicability,
   custom per-record protection and aggregate pre-checks each block the entire operation when one check fails.
   Hidden blocker details remain hidden.
6. Confirming after a selected record disappears, loses access, changes parent, falls outside the submitted
   source filter or becomes protected deletes nothing and explains the need for fresh selection/review.
7. Confirmation displays the fixed selection and permitted deletion effects, requires explicit confirmation,
   and offers cancel/back. A blocked selection has no executable delete control. Previews respect existing
   visibility, completeness and display-limit semantics; display limits do not change the deletion selection.
8. A failure on a later record rolls back earlier database writes. No partial-success message or success
   callback is emitted. Native protection and unexpected exceptions retain their documented distinctions.
9. Forged IDs, changed parent/view/action context, unconfigured actions, over-limit POSTs, stale confirmation,
   invalid IDs and empty selections cannot bypass validation or silently reduce the selected set.
10. A documented custom action uses the shared public API, including a whole-selection check, without a
    matching single-record view. Customization boundaries and transaction/side-effect limitations are explicit.
11. Existing single-record delete behavior and normal list/card rendering remain unchanged. Unsupported
    Resource/multi-database/customization cases fail clearly before writes rather than weakening safeguards.
12. The new reference documentation and separate multi-example app described in D-10/A-05 ship together,
    with working navigation, reproducible seeds, source pointers and reciprocal links.
13. Focused Python tests cover authorization, selection, limits, rollback and supported deletion semantics;
    browser checks cover tables/cards, pagination, confirmation, blocked outcomes, keyboard use and a narrow
    viewport. Run the appropriate existing regression suites with multicore pytest for broad runs.

## Implementation references

- `src/crud_views/lib/views/list.py`, `views/card.py`, `views/mixins.py`: current list/card and filter surfaces.
- `src/crud_views/lib/table/table.py`: table action-column placement and view context.
- `src/crud_views/lib/views/delete.py`: protection hook, confirmation and delete write lifecycle.
- `src/crud_views/lib/deletion.py`: inspection, provider boundaries and execution safeguards.
- `src/crud_views/lib/view/base.py`, `crud_views_guardian/lib/mixins.py`: request gates versus button access.
- `src/crud_views_guardian/lib/views.py`: protected/cascade-label visibility.
- `docs/reference/delete_view.md`, `request_lifecycle.md`, `resources.md`: existing guarantees/limitations.
- `examples/bootstrap5/project/features.py`: dedicated example-app navigation and reciprocal doc references.

## Open review points

- Review the proposed defaults and storage mechanism; the mockup approved behavior, not a specific storage API.
- Ensure the customization contract and overlap behavior can be implemented simply without silently weakening
  single-record deletion rules. A concrete conflict must be brought back instead of expanding into a generic
  view replay or transaction framework.
