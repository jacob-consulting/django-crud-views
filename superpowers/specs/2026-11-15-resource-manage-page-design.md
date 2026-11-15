# Design: manage pages for Resource ViewSets

**Date:** 2026-11-15
**Status:** approved by the maintainer on 2026-11-15; ready for GSD planning. Implementation pending.
**Issue:** [django-crud-views#372](https://github.com/jacob-consulting/django-crud-views/issues/372).
**Baseline:** merged #366 and #370; source inspected at `04f95c30` on `origin/main`.

## Intent and scope

The maintainer uses standalone S3 objects as Resources in a downstream project. Give these ViewSets the
existing developer manage page, and support Resources nested beneath model-based ViewSets as well.
Developers should inspect configuration, permission holders, views, routes and checks without fetching
Resource items. Explicit access checks retain the existing ability to exercise Resource reads.

This is a bounded extension of the existing page, not a new diagnostics subsystem. Preserve model and
Guardian manage behavior, template extension points and existing data-method contracts. Avoid additional
queries on existing model paths and avoid an abstraction layer for two kinds of identity metadata.

## Approaches

1. **Extend `ManageView` — selected by the maintainer.** Reuse registration, data builders, templates,
   authorization and access tracing. Add explicit Resource handling where metadata or display differs.
   This keeps behavior together and limits ongoing maintenance; Resource branches must stay small.
2. **Separate Resource manage view — rejected.** It could isolate Resource-specific rendering, but would
   add another class and customization surface while most behavior remains shared.

## Decisions

### D-01: Registration and access

Register the existing manage view for Resource ViewSets, using the same `manage_view_class` selection,
route conventions and manage-action insertion rules as model ViewSets. Keep existing manage settings;
introduce no Resource-specific enable switch. A Resource manage route needs no Resource object identifier.

Keep the active, authenticated developer-group requirement, including its treatment of staff and
superusers, and the existing enabled/disabled/debug-only modes. Resource permission mappings do not
authorize entry to the manage page. Automatic registration must work with an empty mapping and must
not cause E260 to demand a fictitious Resource permission for the manage view.

### D-02: Standalone and nested Resources

Support both standalone Resources and Resource leaves beneath model-based ViewSets. For nested pages,
preserve parent URL coordinates, existing ancestor policy and authorization order: parent authorization
before local manage authorization and diagnostic permission-holder reads. Keep the existing nested
database restrictions, including when the model ancestor uses Guardian.

The current `_check_nested_auth` already recognizes Resource leaves; its ordinary auth-table path does
not inspect the Resource as an ORM model. Verify the actual request and action-visibility paths before
changing it. Do not weaken these guards or add Resource object grants.

### D-03: Opening the page does not load Resource items

The built-in page must not call the managed Resource's `cv_get_items` or `cv_get_item` merely to show
configuration, permission holders, hierarchy, system checks or routes. Parent-model lookups and Django
auth-table reads remain legitimate. No S3 client or live bucket is required for acceptance tests.

This guarantee concerns built-in behavior; arbitrary downstream overrides or custom system checks can
perform their own I/O. Do not add caching, hook interception or a sandbox to police those extensions.

### D-04: Resource identity and presentation

Identify the backing class as a **Resource**, retain its dotted class path, and display effective names,
PK metadata and ordering from the existing Resource metadata and ViewSet overrides. Label inherited
metadata as Resource metadata rather than model metadata. Preserve declared/default provenance and the
existing Show defaults behavior. Show `resource_permissions` in Presentation.

Keep the existing page layout. In a model parent's Hierarchy card, replace “Resource, no manage page”
with the Resource child's actual manage route information. Preserve the existing distinction between
upward links and child route descriptions; do not invent a parent object to make a child link.

### D-05: Permission matrix and the new label type

Use the explicit `resource_permissions` mapping through `viewset.permissions`; never derive a
ContentType or default permissions from the Resource class. Reuse holder rows, effective actor checks,
user-visibility settings and superuser handling from the existing matrix.

The maintainer requested another label type: successful Resource permission cells display **resource**,
alongside the existing **model** and object-grant labels. Apply it consistently to actor, group, user and
overflow rows. It means a Django permission declared in `resource_permissions`, not a per-item grant.
Explain that meaning in the Resource matrix legend; do not imply Guardian object counts exist there.
Existing model and Guardian labels retain their meanings.

**Approved badge styling:** text `resource`, theme key `manage:badge-resource`, and Bootstrap default
`badge bg-info text-dark`. This distinguishes it from the gray `model` badge and light bordered
object-grant badge. The text carries the distinction independently of color; downstream themes can
override the registry key. Translate the label and explanatory text.

Keep the established permission-cell data shape; the Resource-specific label is a presentation
distinction, not another permission engine.

For `None` or an empty mapping, show a clear “No Resource permissions declared” state with no permission
columns. Do not imply that the manage page or Resource endpoints are public: developer-group access,
ancestor checks and custom view restrictions are separate from that mapping.

### D-06: Reuse access checks

Keep #370's existing opt-in setting, forms, selected-user behavior and trace runner. Do not introduce
a Resource-specific tracing API or an S3 identifier convention.

Configuration and permission displays require no object identifier. Explicit list/non-object checks
need none either. Object-view checks use the identifier already accepted by their URLs; absent an
identifier, retain the existing “needs an object pk” result. Submitted checks may invoke Resource reads
to observe lookup, existence and object-dependent access conditions. They do not execute action handlers.
Preserve existing disclosures about trace limits and external effects; database rollback cannot undo
arbitrary external I/O.

### D-07: Access-trace parity between the UI and `cv_access`

The maintainer explicitly requires parity with the existing `cv_access` management command. This is
part of #372's scope and acceptance, not a dependency on the separate configuration-dump proposal #371.

For the same Resource URL, selected actor and data state, the manage form and command must report the
same outcome, deciding step, ordered observations, permission requirements, Resource identity, counts
where applicable, errors and limitations. Both already call `trace_access`; retain that shared owner.
Test the UI path form and each executable per-ViewSet result against the corresponding command trace.
The per-ViewSet form may produce several traces; compare each with the command for that row's URL.

Cover command text and `--as-json` output as well as HTML. Resource-specific trace facts and explanatory
changes must reach both renderers. Preserve the existing JSON version/schema and command exit behavior
unless a concrete incompatibility is identified and brought back for a decision.

Parity means equivalent diagnostic information, not identical formatting or adding the entire UI
permission-holder matrix to `cv_access`. The new `resource` matrix badge identifies the configured grant
type; it must not relabel the trace's actual Django permission provider as a new backend. Keep those
meanings consistent wherever they appear, without inventing Resource object grants.

Include traces targeting the newly registered Resource manage URLs themselves: they must expose the
same developer-group and nested ancestor decisions through the CLI and UI path form. The inspected
actor need not be the authorized developer hosting the form; compare the same inspected actor in both
interfaces and preserve the existing hosting-page access gate.

## Non-goals

No bucket browser, connectivity probe, S3 configuration discovery, new AWS dependency, Resource Guardian
support, Resource-as-parent support, authorization redesign, new page layout, or configuration CLI (#371).
Do not change Resource identifier encoding or add create/update/delete capabilities.

## Acceptance and documentation

- Standalone and model-nested Resources register and render the shared manage page and its manage action.
- Existing manage modes, developer-group rules, ancestor denials and nested database guards hold for
  both direct requests and relevant action visibility. Denied requests do not reach Resource loaders
  or permission-holder diagnostics.
- Opening an allowed page succeeds with Resource item/list loaders that raise if called.
- Resource identity, declared/default metadata, mapping display and hierarchy routes render correctly.
- Resource permission badges cover actor/group/user/overflow rows, use the theme registry and have
  accurate translated legends; model and Guardian output retain their existing semantics.
- Empty mappings render an explicit empty state and pass valid manage registration/system checks.
- Access checks remain off by default. Enabled checks cover list, object with/without an identifier,
  missing Resource item and nested parent coordinates using fake Resource data.
- Prove UI/`cv_access` parity for matching Resource paths, actors and fixture state: allowed/denied
  permissions, missing items, nested ancestor decisions, and Resource manage URLs. Compare trace data
  with command JSON and check that command text/HTML communicate the same facts and limitations.
- Update manage and Resource references, remove the obsolete “No ManageView” limitation, explain the
  label/theme key and trace read boundary, add German translations and a changelog entry. If a Breaking
  entry is warranted, also update `docs/migrating-1.0.md` under the repository rule.
- Run focused Resource/manage/access-trace tests and appropriate model/Guardian regression coverage;
  use multiple pytest workers for broad runs. Check rendered output in English and German.

## Implementation discretion

Exact helper placement, additional context fields, template conditionals and test organization remain
implementation choices. Prefer existing contracts and small local changes. No phase number or execution
plan is assigned by this design; it supersedes only the earlier exclusion of Resource manage pages.

## gsd-handover

### Settled discussion decisions

Carry the following decisions into GSD planning without reopening them absent a concrete conflict.
References D-01–D-07 point to the detailed sections above; the statements below distinguish settled
scope from author-proposed implementation details. The motivating downstream case is standalone S3
objects, but the implementation is for Resources generally.

- **Approach — extend the existing `ManageView`.** The maintainer explicitly selected reuse of the
  existing view over a separate Resource manage view. Keep the existing page layout and data builders;
  use small Resource-specific adaptations instead of a parallel implementation.
- **D-01 — same manage-page behavior and access restrictions.** Automatically register Resource manage
  pages and their manage actions using the existing settings. Keep developer-group restrictions and
  existing manage modes; Resource permissions do not replace authorization to open the manage page.
- **D-02 — standalone and nested support.** Both standalone Resources and Resources below model-based
  ViewSets must work. Preserve parent authorization and parent URL coordinates. Resource leaves do
  not gain Guardian object permissions merely because a model ancestor uses Guardian.
- **D-03 — inspect configuration without loading Resource items.** Opening the built-in page must not
  list an S3 bucket or fetch a Resource object. Existing parent-model and auth-table reads are allowed.
  Resource reads belong to explicitly submitted access checks, subject to the existing trace limits.
- **D-04 — Resource-aware diagnostics.** Reuse the existing cards, showing Resource identity and metadata,
  the explicit permission mapping, and actual hierarchy routes in place of the old no-manage-page label.
- **D-05 — explicit permissions and a new `resource` label.** The maintainer explicitly requested another
  permission label type alongside `model` and object grants. Resource permission cells must identify
  grants from `resource_permissions`, without implying per-object grants. Apply the distinction to all
  matrix row kinds and provide a clear empty state when no Resource permissions are declared.
  **Badge styling is approved:** text `resource`, theme key `manage:badge-resource`, Bootstrap default
  `badge bg-info text-dark`. Preserve the text distinction and downstream theme overrides.
- **D-06 — reuse the existing access form and identifier contract.** Configuration, the permission matrix
  and non-object access checks need no Resource identifier. Object-view traces require the existing
  URL identifier to observe lookup, missing items and object-dependent conditions. Without it, retain
  the existing “needs an object pk” behavior. Introduce no S3-specific identifier convention.
- **D-07 — UI/`cv_access` parity is in scope.** The maintainer clarified that the management command in
  question is `cv_access`, not #371's configuration dump. Use the shared trace runner and prove matching
  diagnostic results for the same URL, actor and data state. Cover text, JSON, the UI path form and
  executable per-ViewSet traces, including the new Resource manage URLs.

### Design defaults and implementation discretion

The following author-proposed defaults are included in the approved design. Details explicitly left
to the builder remain implementation choices rather than separately prescribed maintainer decisions:

- Preserve the existing permission-cell data structure. Internal presentation plumbing remains an
  implementation choice; the Resource label, theme key and default badge classes are settled in D-05.
- Use the existing metadata/default-provenance mechanisms and hierarchy route builders. Exact helper
  placement, context additions and empty-state wording remain planning discretion.
- Verify `_check_nested_auth` against real Resource manage requests before considering changes. Source
  inspection suggests its ordinary auth-table path is compatible; that is evidence to test, not an
  acceptance result or a reason to bypass the guard.

### Acceptance criteria for the phase plan

The plan must turn the detailed acceptance section above into executable checks, covering at least:

1. **Registration and authorization:** standalone and model-nested Resource manage pages, action
   visibility, all existing manage modes, developer membership, ancestor denial and nested database
   boundaries. Empty Resource permission mappings must not break manage registration/system checks.
2. **No implicit Resource reads:** render an authorized default page with both Resource loaders set to
   fail if called. Prove denied requests do not reach Resource loaders or holder diagnostics.
3. **Accurate diagnostics:** Resource class/metadata, declared/default values, explicit permission
   mapping, empty state and parent/child hierarchy route information.
4. **Permission labels:** `resource` badges across actor/group/user/overflow rows, correct explanatory
   text and theme integration; preserve existing model/Guardian labels and permission behavior.
5. **Access-check reuse:** default-off behavior, explicit list and object checks, missing identifiers,
   missing items and nested coordinates, using fake Resource data without S3 credentials or live calls.
6. **UI/CLI parity:** compare form trace data with `cv_access --as-json` for the same path, actor and
   fixture state. Check text and HTML presentation of the same facts, errors and limitations, including
   Resource and nested manage routes. Preserve the actual permission-provider meaning and existing
   CLI contract; UI matrix badges do not introduce a new backend or command mode.
7. **Compatibility and delivery:** Resource/manage/access-trace tests, relevant model/Guardian regression
   coverage, English/German rendered output, translated strings, theme documentation, updated Resource
   and manage references, and a changelog entry. Follow the repository's migration rule for any Breaking
   entry and use multicore pytest for broad verification.

### Boundaries and next workflow

Build on merged #366 and #370. Include `cv_access` parity under D-07; keep #371 separate. Do not expand
into Resource-as-parent support, Resource Guardian integration, S3 browsing/connectivity tools, new
write capabilities or a new tracing engine. Preserve proven authorization paths and avoid new query
costs on model-based manage pages.

The maintainer approved this design and handover on 2026-11-15. The issue is ready for GSD planning;
approval does not assign a phase number, create a worktree or execute the feature. Use this handover
and the detailed design as planning inputs. Surface any concrete conflict with a settled decision
instead of silently widening scope or redesigning the existing manage page.
