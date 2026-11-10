---
last_mapped_commit: a025ddf096a6d4bd28bde23c8b5eb9a4eb687844
last_mapped_at: 2026-11-10
---
<!-- refreshed: 2026-11-10 -->

# Architecture

**Analysis Date:** 2026-11-10

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                    Django host project / application                     │
│ ViewSet declarations + CrudView subclasses + host templates/config       │
│ `examples/bootstrap5/` · consumer applications                            │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │ class creation / URL inclusion
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Core orchestration: `src/crud_views/lib/viewset/` + `lib/view/`           │
│ Registry, URL patterns, sibling links, context, permissions, checks        │
└───────────────┬───────────────────┬────────────────────┬─────────────────┘
                │                   │                    │
                ▼                   ▼                    ▼
┌─────────────────────┐ ┌────────────────────┐ ┌─────────────────────────┐
│ Generic Django CBVs │ │ Optional extensions│ │ Presentation adapters   │
│ `lib/views/`        │ │ `src/crud_views_*` │ │ templates, tags, CSS/JS │
└──────────┬──────────┘ └──────────┬─────────┘ │ `templates/`, `static/` │
           │                       │           └────────────┬────────────┘
           └───────────────────────┴────────────────────────┘
                                   ▼
             Django ORM models or `Resource` data providers
             HTTP response / rendered page or modal partial
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| ViewSet registry and router | Pydantic-configured model/resource registry, view registration, URL generation, parent filtering, permission maps | `src/crud_views/lib/viewset/__init__.py` |
| Parent relationship descriptor | Names and resolves parent ViewSets, URL PK args and model relationship attributes | `src/crud_views/lib/viewset/parentviewset.py` |
| View registration metaclass | Registers a class with its `cv_viewset` and adopts the ViewSet model by default | `src/crud_views/lib/view/meta.py` |
| CrudView integration base | Sibling/action resolution, context, routing, message rendering, access policy, write transaction hooks | `src/crud_views/lib/view/base.py` |
| Django generic views | List/card/detail/create/update/delete, action, child and manage request handlers | `src/crud_views/lib/views/` |
| Presentation model | Button/action grouping, context, labels, variants, visibility and metadata | `src/crud_views/lib/view/` |
| Asset and theme delivery | Registry of app-contributed JS/CSS and theme-template tags/config | `src/crud_views/lib/assets.py`, `src/crud_views/templatetags/crud_views.py` |
| Object detail extension | Configurable property groups, typed property resolvers, layout templates, detail view integration | `src/crud_views_object_detail/lib/` |
| Workflow extension | FSM transition form actions and workflow history/audit model | `src/crud_views_workflow/lib/` |
| Polymorphic extension | Type selection and model-specific create/update/detail views | `src/crud_views_polymorphic/lib/` |
| Guardian extension | Object permission-aware ViewSet, view mixins, permission management screens | `src/crud_views_guardian/lib/` |
| Resource abstraction | Pydantic-backed, non-ORM row contract for read-oriented views | `src/crud_views/lib/resource.py` |
| Startup validation | Django checks over registered ViewSets, views, templates, asset declarations and extension configuration | `src/crud_views/checks.py`, `src/crud_views_workflow/checks.py`, `src/crud_views_guardian/checks.py` |
| Ancestor authorization engine | Request-local guard for nested ViewSets: static ancestry validation, actor admission, outermost-inward ancestor resolution and permission gates, child/parent membership checks | `src/crud_views/lib/ancestors.py` |
| Ancestor policy values | Strict Pydantic `AncestorPolicy` / `AncestorPermissions` (provider, cascade, read/write/action permission pairs) | `src/crud_views/lib/ancestor_policy.py` |
| Nested default-database boundary | Refuses non-`default` aliases for nested ORM data, writes and authorization records | `src/crud_views/lib/ancestor_db.py` |
| Guardian ancestor provider | Object-permission gate for a `GuardianViewSet` used as an ancestor | `src/crud_views_guardian/lib/ancestors.py` |
| Delete preview and protection | Bounded related-object preview, protected-row labels, and deletion lifecycle integration | `src/crud_views/lib/deletion.py`, `src/crud_views/lib/views/delete.py`, `src/crud_views/templates/crud_views/snippets/delete/` |

## Pattern Overview

**Overall:** Registry-driven composition of Django class-based views with a reusable server-rendered Bootstrap 5 presentation layer.

**Key Characteristics:**
- A `ViewSet` instance is the central router and shared configuration boundary. A concrete view joins it declaratively through `cv_viewset` and `cv_key`.
- Form Cancel navigation is resolved per request through `cv_get_cancel_url()` and exposed to the form-button renderer; resolution accounts for access, nested objects, and request origin/query state (`src/crud_views/lib/view/base.py`, `src/crud_views/lib/view/button_data.py`).
- Protected-delete previews have a bounded display budget and render protected-object references as plain labels (`src/crud_views/lib/deletion.py`, `src/crud_views/templates/crud_views/snippets/delete/protected_objects.html`).
- Workflow transitions use the shared form-frame and themeable presentation contracts; the documented opt-in page gate uses explicit transition rules and is covered by request tests (`src/crud_views_workflow/lib/views.py`, `src/crud_views_workflow/templates/crud_views_workflow/`, `tests/test1/`).
- Nested requests pass through one ancestor-authorization guard (`_authorize_ancestors`) before any endpoint work: it resolves each ancestor through its own ViewSet queryset, applies per-ancestor permission gates (provider `model`, `guardian` or `none`; full cascade or nearest-only) and stores the resolved chain on the view instance (`src/crud_views/lib/ancestors.py`). Top-level requests do no ancestor work.
- `CrudViewMetaClass` performs registration during class creation; consumers include the ViewSet's `urlpatterns` from their Django URL configuration.
- Concrete request handlers combine the package's `CrudView` mixin with Django generic CBVs; permission-required classes add `CrudViewPermissionRequiredMixin`.
- The core theme is implemented in Django templates and template tags. App-contributed behavior can add static assets through `register_assets()` from an app's `AppConfig.ready()`.
- Object-detail tabs are scoped by `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js` and delegate lifecycle to `cv.adapters.tab`. Accordion templates render Bootstrap `data-bs-toggle="collapse"`, target, and parent attributes; `presentation.selected` sets initial classes and ARIA state, while Bootstrap's existing Collapse data API handles switching and close-all behavior (`src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html`).
- Optional packages depend on the core public view abstractions and are enabled by installing their app and declaring their specialized views.

## Layers

**ViewSet and registration layer:**
- Purpose: Collect related views and derive consistent names, URLs, parent relations and permissions.
- Location: `src/crud_views/lib/viewset/`, `src/crud_views/lib/view/meta.py`
- Contains: `ViewSet`, `ParentViewSet`, PK path regexes, and `CrudViewMetaClass`.
- Depends on: Django model metadata and URL APIs, Pydantic, `CrudView` definitions.
- Used by: Consumer URL configuration, views, template context and system checks.

**Request and domain integration layer:**
- Purpose: Handle HTTP dispatch and CRUD behavior while preserving ViewSet sibling awareness.
- Location: `src/crud_views/lib/views/`, `src/crud_views/lib/view/base.py`
- Contains: CRUD CBVs, action/order operations, card/list views, create-parent mixins and form processing.
- Depends on: Django CBVs/ORM/forms, optional `django-filter`, `django-tables2`, crispy forms integrations.
- Used by: Django URL dispatch and extension-package subclasses.

**Shared behavior and presentation layer:**
- Purpose: Compute action visibility, button data, labels, breadcrumbs, icons, settings, messages, forms and list/table support.
- Location: `src/crud_views/lib/view/`, `src/crud_views/lib/conditional/`, `src/crud_views/lib/formsets/`, `src/crud_views/lib/table/`, `src/crud_views/lib/crispy/`
- Contains: Focused helpers and presentation data models; theme settings are centralized in `src/crud_views/lib/settings.py`.
- Depends on: View/ViewSet configuration, request/user state, and optional Django presentation packages.
- Used by: CBVs, template tags and the core theme.

**Theme and browser layer:**
- Purpose: Render complete views and reusable components, and supply progressive-enhancement JavaScript.
- Location: `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/`
- Contains: View templates, theme partials/tags, button/action templates, modal shell/content, table/formset templates, CSS and JS adapters.
- Depends on: Django template context and Bootstrap 5 conventions; integrations may provide optional JavaScript adapters.
- Used by: Host templates loading `{% load crud_views %}` and extending the configured base template.

**Extension applications:**
- Purpose: Add specialized view behavior without placing optional dependency coupling in the core request handlers.
- Location: `src/crud_views_object_detail/`, `src/crud_views_workflow/`, `src/crud_views_polymorphic/`, `src/crud_views_guardian/`
- Contains: App configs, Python extensions, translations, and where needed their own templates, static assets and migrations.
- Depends on: Core `CrudView`/ViewSet APIs plus the corresponding optional Django ecosystem package.
- Used by: Consumer projects that install and configure the extension.

**Object-detail layout adapter:**
- Purpose: Render property groups into layout packs and initialize interactive tabs while keeping UI-library ownership behind the theme adapter API.
- Location: `src/crud_views_object_detail/lib/presentation.py`, `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/`, `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`
- Contains: Per-render component identity/presentation data, layout templates and scoped tab lifecycle bridge. Accordion initial selected state is projected into CSS classes and ARIA attributes by the templates; Bootstrap's Collapse data API owns subsequent interaction.
- Depends on: Core asset registry and `cv.adapters` contracts.
- Used by: Object-detail pages and modal content in consumer projects.

## Data Flow

### Primary Request Path

1. The consumer declares a `ViewSet` and associates `CrudView` subclasses using `cv_viewset`; class creation registers the view in `src/crud_views/lib/view/meta.py`.
2. Django resolves a generated pattern from `ViewSet.urlpatterns` (`src/crud_views/lib/viewset/__init__.py`), matching the ViewSet prefix, optional ancestor prefixes/PKs, object PK and view path.
3. The concrete CBV dispatches the request. `CrudView` supplies sibling URL/context behavior, model defaults and optional permission-aware action state (`src/crud_views/lib/view/base.py`).
4. Object querysets are obtained from the ViewSet and filtered by parent attributes for nested ViewSets; Resource-based views instead use resource-specific mixins and row-provider methods (`src/crud_views/lib/resource.py`).
5. The CBV renders a full page or configured content partial; template tags resolve the view context and render theme components (`src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/`).

### Nested Request Path (ancestor authorization)

1. `CrudView.dispatch()` calls `_cv_ancestor_guard()`; permission-required views reach the engine through `CrudViewPermissionRequiredMixin.dispatch`, Guardian views through `GuardianParentPermissionMixin.dispatch`, manage views through `ManageView.dispatch` (`src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/`, `src/crud_views_guardian/lib/mixins.py`).
2. `_authorize_ancestors(view)` validates declared ancestry via `_walk_ancestors` (bounded, no DB), selects the operation's permission pair from `_operation_family` (finite table; custom actions need an exact `ancestor_policy.actions` entry) and the gated levels (`src/crud_views/lib/ancestors.py`).
3. Actor admission runs before any lookup via `_cv_ancestor_actor_response(protected=...)`: anonymous gets login redirect (Guardian: configured 403/404), inactive 403.
4. Ancestors resolve outermost inward through each ViewSet's queryset (404 when missing); each selected gate checks `ancestor_db._check_nested_auth` (default database only) then the provider (403 on denial).
5. The resolved `_AncestorState` is cached on the view; `cv_get_parent_object()` reuses it. `CrudView.get_object` calls `_validate_child_parent` and list views `_scope_child_queryset`, so a child queryset override cannot leak another parent's rows; Resource leaves are skipped.
6. Nested ORM data, writes and delete aliases are restricted to the `default` database by `src/crud_views/lib/ancestor_db.py`.

Configuration: per-ViewSet `ViewSet.ancestor_policy` (`AncestorPolicy`) plus global `CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE`, `CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS`, `CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS` in `src/crud_views/lib/settings.py`. Structure/action declaration problems surface as system checks in `src/crud_views/checks.py`. Docs: `docs/reference/nested.md`, `docs/reference/guardian.md`.

### Asset and Theme Flow

1. Core assets are selected from `CrudViewsSettings`; extensions may register bundles during `AppConfig.ready()` (`src/crud_views/lib/assets.py`).
2. `{% cv_css %}` and `{% cv_js %}` render enabled bundle entries; optional django-pipeline integration consumes lazy sources from `src/crud_views/lib/pipeline.py`.
3. The theme's shared templates and JavaScript adapters initialize configured behavior such as modals, tooltips, list filters, formsets and action controls (`src/crud_views/templates/crud_views/shared/`, `src/crud_views/static/crud_views/js/`).
4. `src/crud_views_object_detail/apps.py` registers the object-detail script bundle; `tabs.js` initializes/disposes marked tab triggers on document readiness and modal load/unload. Accordion `presentation.selected` determines initial expanded/collapsed classes and `aria-expanded`; Bootstrap's data API handles later trigger clicks and parent-scoped collapse behavior (`src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html`, `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`).

### Extension Flow

1. Consumer installs an extension app and imports its public classes from the app package/lib public API (for example `src/crud_views_object_detail/lib/__init__.py`).
2. Specialized views subclass core CBVs or mixins; extension `AppConfig.ready()` registers system checks or assets where applicable.
3. Extension templates and static assets override/extend the core output through Django's template/static lookup mechanisms.

**State Management:**
- ViewSet instances and the asset registry are process-level registries protected by locks where mutation is shared (`src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/assets.py`).
- Per-request state lives on Django view instances, request/session data, and the generated `ViewContext` (`src/crud_views/lib/view/context.py`).
- CRUD writes are atomic by default through `CrudView.cv_atomic` and the view processing hooks in `src/crud_views/lib/view/base.py`; database aliases are resolved by the view.
- Resource rows are obtained per request from a consumer-defined `Resource.cv_get_items()` or `cv_get_item()` rather than stored in the Django ORM (`src/crud_views/lib/resource.py`).

**Workflow transition execution:** `WorkflowView` and public `run_transition()` share the private engine in `src/crud_views_workflow/lib/execution.py`. It verifies the selected database alias and persisted actor/object identity, validates availability/business/comment policy, then saves model state and `WorkflowInfo` within one alias-specific atomic block. View follow-ups use `transaction.on_commit()` on that same alias (`src/crud_views_workflow/lib/views.py`).

### Object-Detail Resolution and Presentation

1. `ObjectDetailMixin.get_property_display()` selects list, exact-model mapping or dynamic configuration; `get_context_data()` forwards the view to shared resolution (`src/crud_views_object_detail/lib/mixins.py`). Complete object-detail views already contain this mixin; compose it first only with core/Guardian/polymorphic views that lack it (`docs/reference/object_detail_view.md`).
2. `resolve_property()` walks terminal field metadata and the existing runtime path. The runtime walk returns raw value plus scalar owner; `_resolve_value()` remains the value-only wrapper (`src/crud_views_object_detail/lib/resolvers.py`). Collection expansion/order and query behavior remain intact.
3. Help instructions resolve explicit lazy/string text, property booleans, nullable view policy, then cached project policy. Only terminal metadata supplies automatic help; resolution does not mutate shared configuration.
4. `ResolvedProperty.value` stays raw; `choice_label` is additive. The value tag dispatches badge → explicit template → choice text → ordinary type and passes both raw `value` and presentation `display_value` (`src/crud_views_object_detail/templatetags/crud_views_object_detail.py`).
5. Stock char/text/default leaves mark exact None/empty display strings. Badge/custom/relation/collection handling retains its separate contract; copied templates require explicit adoption (`docs/migrating-1.0.md`).

## Key Abstractions

**ViewSet:**
- Purpose: Shared model/resource, URL, permission and presentation configuration for a family of views.
- Examples: `src/crud_views/lib/viewset/__init__.py`, `examples/bootstrap5/library/views.py`, `examples/bootstrap5/nested/views.py`
- Pattern: Instantiate once, then register view classes by declaring `cv_viewset` and unique `cv_key`; include its generated URL patterns.

**CrudView:**
- Purpose: Cross-cutting mixin enabling sibling links, context, access-aware action resolution and standard CRUD settings.
- Examples: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/list.py`, `src/crud_views/lib/views/create.py`
- Pattern: Mix into a Django generic CBV; use package-provided concrete classes for standard operations.

**ParentViewSet:**
- Purpose: Describe the parent ViewSet and relation used in nested URLs and child queryset constraints.
- Examples: `src/crud_views/lib/viewset/parentviewset.py`, `examples/bootstrap5/nested/views.py`
- Pattern: Declare a child ViewSet with a parent reference and a FK/relationship attribute; use parent-aware create behavior for new children.

**AncestorPolicy:**
- Purpose: Typed, stateless per-ViewSet configuration of ancestor authorization (strict: no coercion, no extra fields).
- Examples: `src/crud_views/lib/ancestor_policy.py`, `ViewSet.ancestor_policy` in `src/crud_views/lib/viewset/__init__.py`
- Pattern: `provider` / `accept_global_perms` apply when the ViewSet is an ancestor; `cascade` / `read` / `write` / `actions` apply to requests targeting it. Construction-time constraints are validated in `ViewSet._validate_ancestor_policy()`.

**Resource:**
- Purpose: Supply read-oriented table/list data without requiring a Django model.
- Examples: `src/crud_views/lib/resource.py`, Resource view support in `src/crud_views/lib/views/`
- Pattern: Define typed Pydantic rows and implement `cv_get_items()`; do not use model write views because Resource ViewSets are explicitly read-only.

**Table:**
- Purpose: django-tables2 base table that carries the view context and an `actions` (`ActionColumn`) column.
- Examples: `src/crud_views/lib/table/table.py`, `tests/test1/test_table_meta.py`
- Pattern: Without a `sequence` kwarg or `Meta.sequence`, `Table.__init__` defaults to `("...", "actions")` so actions render last. A declared `Meta.sequence` is used as written (it should name `"actions"` to place it; otherwise django-tables2 places it first among unlisted columns). A caller `sequence` kwarg wins over both. Remove the column with `Meta.exclude = ("actions",)` (Phase 06.19, #337).

**Presentation contract:**
- Purpose: Pass normalized semantic action/button/context data from Python to templates.
- Examples: `src/crud_views/lib/view/action_menu.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/view/context.py`, `src/crud_views/lib/view/button_data.py`
- Pattern: Resolve presentation through the helpers and template tags rather than constructing markup in view code.

## Entry Points

**Django app initialization:**
- Location: `src/crud_views/apps.py`
- Triggers: Django app registry startup.
- Responsibilities: Register core system checks via `ready()` importing `crud_views.checks`.

**ViewSet URL inclusion:**
- Location: `src/crud_views/lib/viewset/__init__.py` (`ViewSet.urlpatterns`)
- Triggers: Consumer URLconf includes the ViewSet patterns.
- Responsibilities: Convert registered view classes into named Django routes and attach the generated dispatch callbacks.

**View class registration:**
- Location: `src/crud_views/lib/view/meta.py`
- Triggers: Import-time class creation when a subclass declares `cv_viewset`.
- Responsibilities: Validate key presence, register the class, and inherit the configured model when omitted.

**Theme template tags:**
- Location: `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templatetags/crud_views_formsets.py`
- Triggers: Django template rendering after host templates load the tag libraries.
- Responsibilities: Expose view/action context and render theme components/forms.

## Architectural Constraints

- **Threading:** Django request handling follows the host server's model; module registries use `threading.Lock` for registration/snapshot operations in `src/crud_views/lib/viewset/__init__.py` and `src/crud_views/lib/assets.py`.
- **Global state:** `_REGISTRY` stores named ViewSets in `src/crud_views/lib/viewset/__init__.py`; `_REGISTRY` stores asset bundles in `src/crud_views/lib/assets.py`; settings are loaded as `crud_views_settings` in `src/crud_views/lib/settings.py`.
- **Circular imports:** `src/crud_views/lib/resource.py` is intentionally kept as a leaf and documents that importing any `viewset` module from it triggers a cycle through `viewset/__init__.py`.
- **Ancestor guard ordering:** The guard must run before an endpoint's own `has_permission()` or state loading; new view compositions must reach `_authorize_ancestors` via one of the existing dispatch bridges. Wave one supports only the `default` database for nested requests (`src/crud_views/lib/ancestor_db.py`).
- **Import-time registration:** View class declarations require their ViewSet to exist first and can fail on duplicate keys/names; keep declaration/import order explicit (`src/crud_views/lib/view/meta.py`, `src/crud_views/lib/viewset/__init__.py`).
- **Theme coupling:** The bundled presentation targets Bootstrap 5 and Django templates; theme-facing changes should update the matching template, Python context/tag contract, and browser behavior where relevant (`src/crud_views/templates/crud_views/`, `src/crud_views/lib/view/`, `src/crud_views/static/crud_views/`).
- **Adapter boundary:** Package-owned browser modules should use semantic methods on `cv.adapters` when they implement behavior through a UI library. Object-detail tabs are explicitly marked and disposed on modal unload; accordion markup relies on Bootstrap's declarative Collapse data API instead (`src/crud_views/static/crud_views/js/adapters.js`, `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`, `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html`).
- **Optional dependencies:** Keep integrations in their dedicated extension packages or guarded core integration modules, and use the public core classes where supported (`src/crud_views_workflow/`, `src/crud_views_polymorphic/`, `src/crud_views_guardian/`, `src/crud_views/lib/crispy/`).

## Anti-Patterns

### Bypassing ViewSet sibling resolution

**What happens:** A view or template hard-codes sibling URLs instead of using the CrudView/ViewSet URL and context APIs.
**Why it's wrong:** Nested prefixes, PK types, namespace names and access-aware action behavior are centrally derived and can diverge from hard-coded paths.
**Do this instead:** Resolve URLs and actions through `CrudView.cv_get_url()`, `cv_get_context()` and template tags in `src/crud_views/lib/view/base.py` and `src/crud_views/templatetags/crud_views.py`.

### Rendering presentation directly from request handlers

**What happens:** View code emits Bootstrap markup or duplicates action selection logic.
**Why it's wrong:** It bypasses normalized presentation data and makes full-page, modal and theme rendering inconsistent.
**Do this instead:** Return context through `CrudView` and render reusable theme components in `src/crud_views/templates/crud_views/` via the corresponding tag/context helpers.

## Error Handling

**Strategy:** Fail fast for invalid static configuration, use Django's standard HTTP exceptions and form validation for request errors, and expose system-check messages for startup-time diagnostics.

**Patterns:**
- `cv_raise()` raises package-specific configuration errors for invalid registry/view operations (`src/crud_views/lib/exceptions.py`).
- Django `Http404`, permission handling and form errors are used at the request boundary (`src/crud_views/lib/views/`, `src/crud_views/lib/view/base.py`).
- Checks are yielded from ViewSets and extensions, then registered with Django (`src/crud_views/checks.py`, `src/crud_views_workflow/checks.py`, `src/crud_views_guardian/checks.py`).
- Database writes follow the transaction boundary controlled by `cv_atomic` and `cv_on_commit()` (`src/crud_views/lib/view/base.py`).

## Cross-Cutting Concerns

**Logging:** No package-wide application logging layer is present; Django and host application logging remain in control.
**Validation:** Pydantic validates ViewSet, Resource and object-detail configuration; Django forms and startup system checks validate request data and package configuration (`src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/resource.py`, `src/crud_views_object_detail/lib/config.py`, `src/crud_views/checks.py`).
**Authentication:** Nested requests additionally authorize every protected ancestor (`src/crud_views/lib/ancestors.py`). Core permission-required CBVs integrate Django's permission mixins; Guardian adds object-level permission checks in `src/crud_views_guardian/lib/`.

## Permission declaration diagnostics (Phase 06.22)

- `check_ancestor_declarations` first completes the configured URL resolver tree, snapshots the ViewSet registry, and runs completion-dependent checks only when that barrier succeeds (`src/crud_views/checks.py`).
- `_permission_key_messages` checks only registered core permission-required views. `_ancestor_pair_messages` walks ancestry, selects protected gates, and checks only pairs consumed by registered endpoints. Both emit `viewset.E269` without querying the database.
- `_concrete_opts`, `_declared_permission_keys`, and `_permission_key` mirror concrete-model runtime vocabulary, including proxy handling and exact terminal suffix removal (`src/crud_views/lib/ancestors.py`).
- `_requirement_source` returns the pair and diagnostic source; `_operation_requirements` delegates to it. Action overrides, explicit family overrides and global defaults retain their established order. Pair diagnostics deduplicate by key and ancestor.
- Guardian/Resource exclusions, E202/E260/E266/E268 ownership, and runtime authorization backstops remain separate. Startup validation establishes declared vocabulary, not persisted auth rows or user grants.

---

*Architecture analysis: 2026-11-10*
