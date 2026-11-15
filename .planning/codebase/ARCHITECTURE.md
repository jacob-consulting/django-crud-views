---
last_mapped_commit: db82bc76f38fdba7396dcdf93e5edd637e44ac8e
last_mapped_at: 2026-11-15
---
<!-- refreshed: 2026-11-15 -->
# Architecture

**Analysis Date:** 2026-11-15

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│ Consumer declarations                                       │
│ ViewSets + CrudView subclasses                              │
│ `src/crud_views/lib/viewset/` `src/crud_views/lib/view/`    │
└──────────────────────────────┬──────────────────────────────┘
                               │ class creation registers views
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Routing and request behavior                                │
│ `src/crud_views/lib/views/` `src/crud_views/lib/ancestors.py`│
└────────────┬─────────────────────┬──────────────────────────┘
             │                     │
             ▼                     ▼
┌──────────────────────┐  ┌──────────────────────────────────┐
│ Django auth / ORM    │  │ Presentation and integrations    │
│ core or Guardian     │  │ templates, forms, tables, assets │
└──────────────────────┘  └──────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| ViewSet registry/router | Stores model and view metadata, registers view classes, derives names/PK routing, and builds URL patterns | `src/crud_views/lib/viewset/__init__.py` |
| View declaration integration | Applies `cv_` attributes, sibling links/context, permission helpers, and ancestor request hooks | `src/crud_views/lib/view/base.py` |
| View registration metaclass | Registers concrete subclasses against their declared ViewSet during class creation | `src/crud_views/lib/view/meta.py` |
| CRUD request handlers | Implements list/detail/create/update/delete/action and manage request lifecycles | `src/crud_views/lib/views/` |
| Nested authorization | Validates ancestry, resolves parent objects, applies inherited permission policy, and scopes child querysets | `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/ancestor_policy.py` |
| Developer manage diagnostics | Projects ViewSet permissions, routes, checks, configuration and optional access traces | `src/crud_views/lib/views/manage.py` |
| Access trace engine | Records authorization results in context-local storage and dispatches a bounded synthetic request | `src/crud_views/lib/access_trace.py`, `src/crud_views/lib/access_trace_runner.py` |
| Guardian extension | Replaces core permission provider and adds object-grant querying and Guardian-specific management | `src/crud_views_guardian/lib/` |
| Optional feature apps | Add object-detail presentation, FSM workflow and polymorphic creation flows | `src/crud_views_object_detail/lib/`, `src/crud_views_workflow/lib/`, `src/crud_views_polymorphic/lib/` |

## Pattern Overview

**Overall:** Declarative ViewSet registry over Django class-based views, with opt-in extension apps and mixins.

**Key Characteristics:**
- A consumer declares a ViewSet and binds CrudView subclasses to it; `CrudViewMetaClass` registers them at import/class-definition time.
- URL generation and sibling-view lookup are centralized on the ViewSet rather than duplicated in consumer URL declarations.
- Django generic views own the standard HTTP/form lifecycle; package mixins add registration, permission, nested-object, and presentation behavior.
- Authorization normally runs in the request path. Access tracing observes reports emitted by those gates and does not run a second policy evaluator.
- Optional integrations are separate installable Django apps and keep provider-specific behavior out of the core path.

## Layers

**Consumer declarations:**
- Purpose: Define the model/resource, route prefix, permissions, nested parent and view classes.
- Location: Consumer application modules; examples live under `examples/bootstrap5/`.
- Contains: `ViewSet(...)` objects and subclasses of exported CRUD views.
- Depends on: Public exports from `crud_views` and optional extension packages.
- Used by: Import-time registration and Django URL configuration.

**Registration and routing:**
- Purpose: Maintain the registry, generate Django URL patterns, and connect routes to registered classes.
- Location: `src/crud_views/lib/viewset/` and `src/crud_views/lib/view/meta.py`.
- Contains: `ViewSet`, `ParentViewSet`, PK converters and metaclass behavior.
- Depends on: Django URL APIs, model metadata, Pydantic configuration.
- Used by: Consumer root URLconf and all sibling-link helpers.

**Request and authorization:**
- Purpose: Execute CRUD handlers and enforce local and inherited access requirements.
- Location: `src/crud_views/lib/views/`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/ancestors.py`.
- Contains: Django CBV subclasses, permission mixins, object lookup, parent resolution and query scoping.
- Depends on: Django auth/ORM and, in the optional extension, django-guardian.
- Used by: Django URL dispatch.

**Presentation and support:**
- Purpose: Build forms, action data, table/formset layouts, templates and static asset behavior.
- Location: `src/crud_views/lib/`, `src/crud_views/templates/`, `src/crud_views/static/`.
- Contains: Cross-view context/presentation helpers and reusable template/UI components.
- Depends on: Django templates and optional crispy-forms, django-tables2 and django-filter packages.
- Used by: CRUD views and application template overrides.

**Extension apps:**
- Purpose: Add optional integrations without requiring every consumer to use them.
- Location: `src/crud_views_guardian/`, `src/crud_views_object_detail/`, `src/crud_views_workflow/`, `src/crud_views_polymorphic/`.
- Contains: App configs, integration-specific views/mixins, templates and translations; workflow also owns audit models/migrations.
- Depends on: Core package and each integration's third-party library.
- Used by: Consumers that install and add the corresponding Django app.

## Data Flow

### Primary Request Path

1. The consumer URLconf includes a ViewSet's generated patterns (`src/crud_views/lib/viewset/__init__.py`).
2. Django resolves the route to a registered view class; class registration happened through `CrudViewMetaClass` (`src/crud_views/lib/view/meta.py`).
3. The view's dispatch and mixins execute ancestor checks, local permission gates, object lookup, and the inherited Django handler (`src/crud_views/lib/view/base.py`, `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/views/`).
4. The handler constructs context/form/table data and renders a package or consumer-overridden template (`src/crud_views/templates/crud_views/`).

### Nested Request Path

1. `ParentViewSet` declarations describe URL ancestry (`src/crud_views/lib/viewset/parentviewset.py`).
2. Ancestor validation and resolution check the configured chain, actor requirements, and selected inherited permission gates (`src/crud_views/lib/ancestors.py`).
3. Child querysets are scoped to the resolved parent; create views can assign the parent FK (`src/crud_views/lib/views/child.py`, `src/crud_views/lib/views/create.py`).
4. Guardian ViewSets use the extension's provider for object-level grants (`src/crud_views_guardian/lib/viewset.py`, `src/crud_views_guardian/lib/ancestors.py`).

### Access Trace Path (Phase 06.34)

1. `cv_access` resolves a username/PK and calls the public `trace_access()` entry point (`src/crud_views/management/commands/cv_access.py`, `src/crud_views/lib/access_trace.py`).
2. The runner resolves only CrudView routes, refreshes the actor, and dispatches a synthetic GET inside a rollback transaction with memory-only session/message stores (`src/crud_views/lib/access_trace_runner.py`).
3. Authorization gates report scalar facts to a `ContextVar` recorder while executing their normal checks (`src/crud_views/lib/view/base.py`, `src/crud_views/lib/ancestors.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views/lib/views/manage.py`).
4. The handler is replaced with a stub, so the trace answers whether the page can be opened without running the real view handler; it records a versioned scalar result and explicit limitations.
5. The manage page can opt into the same engine via `CRUD_VIEWS_MANAGE_ACCESS_TRACE`; query parameters select an explicit user and either a path or current ViewSet (`src/crud_views/lib/views/manage.py`).

## Key Abstractions

**ViewSet:**
- Purpose: Collection-level registry, routing contract and permission metadata.
- Examples: `src/crud_views/lib/viewset/__init__.py`, `src/crud_views_guardian/lib/viewset.py`.
- Pattern: One ViewSet instance is bound to view classes at declaration time; its generated URLs and lookup methods are the source of sibling-route relationships.

**CrudView:**
- Purpose: Shared mixin contract for package CBVs, including ViewSet access and cross-view behavior.
- Examples: `src/crud_views/lib/view/base.py`, concrete handlers in `src/crud_views/lib/views/`.
- Pattern: Combine `CrudView` with a Django generic view and use `cv_` class attributes for package configuration.

**AncestorPolicy:**
- Purpose: Describes which inherited permissions and provider behavior apply to nested requests.
- Examples: `src/crud_views/lib/ancestor_policy.py`, enforcement in `src/crud_views/lib/ancestors.py`.
- Pattern: Declare policy on the child ViewSet; enforcement resolves the real parent chain during requests.

**AccessTrace / AccessRecorder:**
- Purpose: Return an explainable projection of gates encountered during one authorization attempt.
- Examples: `src/crud_views/lib/access_trace.py`, `src/crud_views/lib/access_trace_runner.py`.
- Pattern: Gate code records only scalar facts under a context-local recorder. The diagnostic runner never caches or substitutes authorization decisions; unknown custom behavior and handler-phase checks remain explicit limitations.

**ManageView:**
- Purpose: Developer-only inspection page for a ViewSet's declarations and runtime diagnostics.
- Examples: `src/crud_views/lib/views/manage.py`, `src/crud_views_guardian/lib/views.py`.
- Pattern: Require active authenticated access and configured manage-group membership; diagnostics are separately opt-in where they can perform additional authorization work.

## Entry Points

**Django app initialization:**
- Location: `src/crud_views/apps.py` and each extension's `apps.py`.
- Triggers: Django app loading.
- Responsibilities: Register app-specific checks, translations, and presentation defaults.

**Generated ViewSet URLs:**
- Location: `src/crud_views/lib/viewset/__init__.py`.
- Triggers: Inclusion by the consumer URLconf.
- Responsibilities: Route collection and object operations to registered view classes.

**Access trace command:**
- Location: `src/crud_views/management/commands/cv_access.py`.
- Triggers: `manage.py cv_access <path> <user>` or `--anonymous`.
- Responsibilities: Validate arguments, resolve the actor, render text or versioned JSON, and return outcome-specific exit codes.

**Manage page access trace:**
- Location: `src/crud_views/lib/views/manage.py`.
- Triggers: GET submission when `CRUD_VIEWS_MANAGE_ACCESS_TRACE` is enabled and the hosting manage request passes its normal checks.
- Responsibilities: Run path or ViewSet traces for the explicitly selected user and project route coordinates.

## Architectural Constraints

- **Threading/context:** The ViewSet registry is module-level and guarded by a `threading.Lock`; trace recorder state uses `ContextVar` so concurrent request contexts do not share one recorder (`src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/access_trace.py`).
- **Database effects:** Access traces execute inside a transaction marked for rollback on the default database, and substitute in-memory session/message storage (`src/crud_views/lib/access_trace_runner.py`). Custom gates can still have arbitrary side effects; the runner does not claim general sandboxing.
- **Trace scope:** Only resolved CrudView routes are traced. The diagnostic request is synthetic GET to `http://localhost`; host-dependent rules, other middleware/decorators, and handler-phase checks are not reproduced (`src/crud_views/lib/access_trace_runner.py`).
- **Import-time registration:** Import order matters because view classes register with ViewSets during class construction (`src/crud_views/lib/view/meta.py`).
- **Nested URL shape:** Parent PK arguments belong to URL ancestry while the target ViewSet's PK belongs to the child route (`src/crud_views/lib/viewset/parentviewset.py`, `src/crud_views/lib/viewset/path_regs.py`).
- **Optional integrations:** Guardian, workflow, object-detail and polymorphic packages are separate Django apps with provider-specific behavior (`src/crud_views_guardian/`, `src/crud_views_workflow/`, `src/crud_views_object_detail/`, `src/crud_views_polymorphic/`).

## Anti-Patterns

### Reimplementing sibling route construction

**What happens:** Code hand-builds routes or reverse names instead of asking the owning ViewSet.
**Why it's wrong:** It can lose PK conversion, parent coordinates and registered custom route behavior.
**Do this instead:** Use the ViewSet routing methods in `src/crud_views/lib/viewset/__init__.py` and resolve declared siblings through `CrudView` in `src/crud_views/lib/view/base.py`.

### Duplicating authorization in diagnostics

**What happens:** A diagnostic independently guesses permissions and reports that as the user's access result.
**Why it's wrong:** It diverges from provider, ancestor, object and custom gates in the real request path.
**Do this instead:** Observe existing gate results through the recorder in `src/crud_views/lib/access_trace.py`; keep unobserved behavior labeled as a limitation in `src/crud_views/lib/access_trace_runner.py`.

### Running the real handler during an access trace

**What happens:** A diagnostic executes a list/detail/form handler to decide whether access is granted.
**Why it's wrong:** It can run business logic, render expensive content, or cause writes.
**Do this instead:** Preserve the synthetic request and handler stub in `src/crud_views/lib/access_trace_runner.py`; add only explicitly bounded, rollback-safe gate observations.

## Error Handling

**Strategy:** Use Django's normal 403/404 behavior for requests, package exceptions for invalid ViewSet declarations, and explicit structured outcomes for diagnostics.

**Patterns:**
- Ancestor configuration and lookup failures are validated in `src/crud_views/lib/ancestors.py` and surface as Django/package exceptions in the normal request path.
- `cv_access` maps allowed, denied, not-found, login-redirect, no-route and error results to documented command exit statuses (`src/crud_views/management/commands/cv_access.py`).
- Trace steps may preserve exception class/message as scalar data; `AccessTrace.version` identifies the JSON contract (`src/crud_views/lib/access_trace.py`).

## Cross-Cutting Concerns

**Logging:** No shared request logger is imposed; Django and consumer applications own logging configuration.
**Validation:** ViewSet declaration checks and Django system checks are implemented in `src/crud_views/lib/check.py`, `src/crud_views/checks.py`, and extension check modules.
**Authentication:** Local permissions use Django auth; nested checks use `src/crud_views/lib/ancestors.py`; per-object permissions are added by `src/crud_views_guardian/lib/mixins.py`.
**Presentation:** Context and action projections are prepared by `src/crud_views/lib/view/` and rendered by overridable templates under `src/crud_views/templates/`.

---

*Architecture analysis: 2026-11-15*
