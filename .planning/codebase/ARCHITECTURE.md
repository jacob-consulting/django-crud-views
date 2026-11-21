---
last_mapped_commit: 4feb0196e169745b7ec9bf879abfbfa45c647e92
last_mapped_at: 2026-11-21
---
<!-- refreshed: 2026-11-21 -->
# Architecture

**Analysis Date:** 2026-11-21

Incremental inspection covers `src/`, `tests/`, `docs/`, and `CHANGELOG.md`, including breadcrumb classes and effective table ordering. Other descriptions retain the existing map's scope: ViewSet/CrudView, ancestors, Resource, manage, access trace, bulk selection, templates and the Bootstrap 5 bulk example; extension internals and JavaScript implementation details are summarized from the existing map and file layout.

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Consumer declarations                                                │
│ ViewSet(model|Resource, ...) + CrudView subclasses (cv_viewset=...)  │
│ `src/crud_views/lib/viewset/__init__.py` `src/crud_views/lib/views/` │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ CrudViewMetaClass registers at class creation
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Registry + routing                                                   │
│ `_REGISTRY` (module level), `ViewSet.urlpatterns`, AutoManageView    │
│ `src/crud_views/lib/viewset/` `src/crud_views/lib/view/meta.py`      │
└───────┬───────────────────────┬──────────────────────────┬───────────┘
        │ request               │ diagnostics              │ startup
        ▼                       ▼                          ▼
┌────────────────────┐ ┌──────────────────────────┐ ┌───────────────────┐
│ CrudView.dispatch  │ │ ManageView builders      │ │ System checks     │
│ ancestor guard +   │ │ get_manage_* (9 sections)│ │ `checks.py`       │
│ permission gate    │ │ `views/manage.py`        │ │ `lib/check.py`    │
│ `view/base.py`     │ └───────┬──────────┬───────┘ │ ViewSet.checks()  │
│ `ancestors.py`     │         │          │         └───────────────────┘
└────────┬───────────┘         ▼          ▼
         │          ┌────────────────┐ ┌──────────────────────────────┐
         │          │ cv_manage_view │ │ cv_access / manage trace form│
         │          │ manage_report  │ │ access_trace(+_runner,_export)│
         │          │ (Pydantic v1)  │ │ (Pydantic export v1)         │
         ▼          └────────────────┘ └──────────────────────────────┘
┌──────────────────────┐   ┌─────────────────────────────────────────┐
│ ORM / Resource rows  │   │ Templates, crispy, tables2, filters,    │
│ Guardian grants      │   │ assets registry, template tags          │
└──────────────────────┘   └─────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `ViewSet` (Pydantic model) | Registry entry, PK type detection, path building, `urlpatterns`, permission map, label/action config, auto manage view | `src/crud_views/lib/viewset/__init__.py` |
| `ParentViewSet` | Declares parent name/attribute/pk_name/M2M-through for nesting | `src/crud_views/lib/viewset/parentviewset.py` |
| PK regex constants | `PrimaryKeys` (INT/HEX/UUID/KEY/STR), named-group helpers | `src/crud_views/lib/viewset/path_regs.py` |
| `CrudViewMetaClass` | On class creation with `cv_viewset` in attrs: requires `cv_key`, calls `register_view_class`, copies `model` | `src/crud_views/lib/view/meta.py` |
| `CrudView` | `cv_*` contract: `dispatch` (ancestor guard), URL/context/action helpers, cancel/origin handling, `cv_get_requirement`, `checks()` | `src/crud_views/lib/view/base.py` |
| `CrudViewPermissionRequiredMixin` | Local permission gate (`has_permission`), recorder hooks, `cv_has_access` | `src/crud_views/lib/view/base.py` |
| Concrete views | `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`, `ActionView`, `OrderedUp/DownView`, `CardListView`, `CustomFormView`, `CustomFormNoObjectView`, `RedirectChildView`, each with `*PermissionRequired` | `src/crud_views/lib/views/` |
| View mixins | `CrudViewProcessFormMixin`, `MessageMixin`, `CardOrderMixin`, `ListViewTableMixin`, `ListViewTableFilterMixin` | `src/crud_views/lib/views/mixins.py` |
| Action/button projection | Buttons, button data, action menus, label modes, visibility, cancel target | `src/crud_views/lib/view/buttons.py`, `button_data.py`, `action_menu.py`, `label_mode.py`, `visibility.py`, `cancel.py` |
| Ancestor engine | Walk/validate parent chain, authorize ancestors per request, scope child queryset | `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/ancestor_policy.py`, `src/crud_views/lib/ancestor_db.py` |
| `Resource` / `ResourceViewMixin` | Non-ORM rows via `cv_get_items`/`cv_get_item`; `_meta` duck type (`ResourceOptions`) | `src/crud_views/lib/resource.py` |
| Bulk selection and action form | Opt-in table/card selection plus permission-gated review and transactional execution of selected ORM objects | `src/crud_views/lib/bulk/__init__.py` |
| Object section navigation | Opt-in `NavBar`/`NavItem` declarations, lazy per-view projection, visibility and active-section calculation | `src/crud_views/lib/navbar.py` |
| Breadcrumb presentation | Opt-in hierarchy projection; list/item/active classes use the shared registry | `src/crud_views/lib/breadcrumb.py`, `src/crud_views/templates/crud_views/tags/breadcrumb.html`, `src/crud_views/lib/button_classes.py` |
| Table header presentation | Projects effective bound-column ordering to sort icons and `aria-sort`; creates prefixed sort links | `src/crud_views/templates/crud_views/table/bootstrap5.html` |
| `ManageView` | Developer page; nine `get_manage_*` section builders; `manage_export()` context for complete machine metadata | `src/crud_views/lib/views/manage.py` |
| Manage report contract | Pydantic wire models, `adapt_section`, `Report` TypeAdapter, `report_schema()` | `src/crud_views/lib/manage_report.py` |
| `cv_manage_view` command | Catalogue/inspection of registered ViewSets, text or JSON, schema mode | `src/crud_views/management/commands/cv_manage_view.py` |
| Access trace model/recorder | `AccessTrace`, `AccessStep`, `AccessRecorder`, `ContextVar` recorder, `trace_access()` | `src/crud_views/lib/access_trace.py` |
| Access trace runner | Synthetic GET, rollback transaction, memory session/messages, handler stub, outcome classification | `src/crud_views/lib/access_trace_runner.py` |
| Access trace export contract | Strict Pydantic v1 wire models, `validate_export()`, `export_schema()` | `src/crud_views/lib/access_trace_export.py` |
| `cv_access` command | Resolves actor, runs trace, validates output, renders text/JSON, exit codes | `src/crud_views/management/commands/cv_access.py` |
| Settings | `CrudViewsSettings` Pydantic model reading `CRUD_VIEWS_*`; module singleton `crud_views_settings` | `src/crud_views/lib/settings.py` |
| System checks | Registered Django checks over the registry, ancestors, conditional, assets, ordering | `src/crud_views/checks.py`, `src/crud_views/lib/check.py` |
| Assets | Asset registry (`register_assets`), django-pipeline sources (`cv_sources`), vendoring | `src/crud_views/lib/assets.py`, `src/crud_views/lib/pipeline.py`, `src/crud_views/lib/vendor.py` |
| Template tags | `cv_css`, `cv_js`, `cv_config`, action/button/context tags, formset tag | `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templatetags/crud_views_formsets.py` |
| Native data-API prefix | Startup-registered scalar (default `bs`); read by rendering tags, config context, theme templates, and object-detail tab selector | `src/crud_views/lib/data_prefix.py`, `src/crud_views/lib/__init__.py`, `src/crud_views/templatetags/crud_views.py` |
| Guardian | `GuardianViewSet`, object/queryset/parent mixins, ancestor provider, `GuardianManageView` | `src/crud_views_guardian/lib/` |
| Object detail | `ObjectDetailView`, property config/resolvers/presentation, own settings | `src/crud_views_object_detail/lib/` |
| Workflow | `WorkflowView` (form per transition), `run_transition`, `WorkflowInfo` audit model | `src/crud_views_workflow/lib/`, `src/crud_views_workflow/models.py` |
| Polymorphic | Select-then-create flow, polymorphic detail/update/delete | `src/crud_views_polymorphic/lib/` |

## Pattern Overview

**Overall:** Declarative ViewSet registry over Django class-based views; opt-in extension apps; diagnostics that project (not re-evaluate) declarations and gate results.

**Key Characteristics:**
- A `ViewSet` instance is bound to view classes through `cv_viewset = my_viewset`; registration happens during class creation (`src/crud_views/lib/view/meta.py`).
- Concrete views multiply-inherit `CrudView` and a Django generic view (e.g. `CreateView(CrudViewProcessFormMixin, CrudView, generic.CreateView)` in `src/crud_views/lib/views/create.py`). Class config uses the `cv_` prefix.
- URL routes are generated by the ViewSet with `re_path`, one per registered key: `^{parent}{prefix}{pk}{view_path}{contribute}$` (`ViewSet.urlpatterns`). Route names come from `get_router_name`.
- Authorization lives in the request path (`CrudView.dispatch` -> `_cv_ancestor_guard` -> `CrudViewPermissionRequiredMixin.has_permission`). Tracing observes gates through the recorder; it never owns a second policy.
- Both machine contracts (`cv_manage_view` report, `cv_access` trace) are strict Pydantic models with an integer `version` and a generated JSON Schema.
- Resource ViewSets are leaves with an explicit `resource_permissions` map and no ORM write views.

## Layers

**Consumer declarations:**
- Purpose: model/Resource, prefix, permissions, parent, view classes.
- Location: consumer apps; reference usage in `examples/bootstrap5/`.
- Depends on: public exports from `crud_views` and extension packages.

**Registration and routing:**
- Purpose: registry, URL patterns, sibling lookup.
- Location: `src/crud_views/lib/viewset/`, `src/crud_views/lib/view/meta.py`.
- Contains: `ViewSet`, `ParentViewSet`, `_REGISTRY`/`_REGISTRY_LOCK`, `PrimaryKeys`.
- Used by: consumer URLconf (`include(viewset.urlpatterns)`), sibling-link helpers, `cv_manage_view`.

**Request and authorization:**
- Purpose: run CBV lifecycle with local and ancestor gates.
- Location: `src/crud_views/lib/views/`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/ancestors.py`.
- Depends on: Django auth/ORM; django-guardian only in `src/crud_views_guardian/`.

**Resource data:**
- Purpose: non-ORM rows through existing list/detail/action handlers.
- Location: `src/crud_views/lib/resource.py`; Resource branches in `src/crud_views/lib/viewset/__init__.py` (`is_resource`, `permissions`, `pk` from `_meta.pk_type`).
- No ContentType permission lookup; `ViewSet.default_permissions` raises for Resources.

**Bulk actions:**
- Purpose: opt-in selection on table/card lists and a destination view that rechecks visibility, per-object authorization and eligibility before applying one action.
- Location: `src/crud_views/lib/bulk/__init__.py`; public exports are `BulkSelectionMixin`, `BulkFormViewPermissionRequired`, and `BulkConfirmForm`.
- Depends on: ORM model ViewSets, normal destination permission and ancestor checks, `cv_get_atomic()`, and `cv_form_valid()`/`cv_form_valid_hook()` for the write. The component is limited to the default database and scalar PK models.
- Presentation: `src/crud_views/templates/crud_views/snippets/bulk_toolbar.html`, `columns/bulk_select.html`, `view_bulk_form.content.html`, and `snippets/bulk/`; progressive enhancement is in `src/crud_views/static/crud_views/js/bulk.js`.
- Consumer example: `examples/bootstrap5/bulk_selection/views.py` shows table and card selection plus bulk delete/archive/owner assignment actions.

**Diagnostics (manage + trace + CLI contracts):**
- Purpose: developer-facing projections of configuration and access.
- Location: `src/crud_views/lib/views/manage.py`, `src/crud_views/lib/manage_report.py`, `src/crud_views/lib/access_trace*.py`, `src/crud_views/management/commands/`.

**Presentation and support:**
- Purpose: forms, tables, formsets, conditional fields, action rendering, assets.
- Location: `src/crud_views/lib/{crispy,table,formsets,conditional}/`, `src/crud_views/lib/{breadcrumb,icons,messages,session,deletion,ordered}.py`, `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/`.

**Theme data-API compatibility:**
- Purpose: let a theme using a compatible native data API choose the attribute prefix without copying prefix-only component templates.
- Location: scalar and validation in `src/crud_views/lib/data_prefix.py`; public startup hook re-exported from `src/crud_views/lib/__init__.py`; render-time consumers in `src/crud_views/templatetags/crud_views.py` and theme templates.
- Lifecycle: `_data_prefix` starts as `bs`; a theme `AppConfig.ready()` calls `register_data_prefix(prefix)`. Values must match `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`; last valid call wins and invalid input raises `ValueError` without mutation. This is startup configuration, not runtime switching or a Django setting.
- Four shipped component templates consume `{% cv_data_prefix %}`: `src/crud_views/templates/crud_views/tags/actions_menu_toggle.html`, `src/crud_views/templates/crud_views/snippets/language_selector.html`, `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/tabs-vertical/object_detail.html`, and `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html`.
- `cv_config` and `cv_const_js` pass the current prefix to `src/crud_views/templates/crud_views/tags/cv_config.html` as `data-data-prefix` on `#cv-config`. `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js` reads it when selecting native tab trigger attributes inside `[data-cv-od-tabs]`, falling back to `bs` if absent. The UI adapter remains separately configured.

**Breadcrumb and table theme contracts:**
- Breadcrumb structure and destinations belong to `src/crud_views/lib/breadcrumb.py`; styling belongs to `src/crud_views/templates/crud_views/tags/breadcrumb.html` and `src/crud_views/lib/button_classes.py`.
- `breadcrumb:list`, `breadcrumb:item`, and `breadcrumb:item-active` default to `breadcrumb`, `breadcrumb-item`, and `active`. Resolve each through package defaults, theme `register_button_classes()`, then project `CRUD_VIEWS_BUTTON_CLASSES`. Empty/non-string values produce an empty contribution; the final item's `aria-current="page"` is independent of classes.
- `src/crud_views/templates/crud_views/table/bootstrap5.html` consumes django-tables2 bound columns for sort state. Preserve `table.thead` for different header semantics. See `docs/reference/buttons.md`, `docs/reference/breadcrumb.md`, `docs/reference/theme.md`, and `docs/reference/list_view.md`.

**Object navigation:**
- Purpose: opt-in identity plus links to owner object views and direct child ViewSets.
- Location: declarations and checks in `src/crud_views/lib/navbar.py`; the three context-preserving rendering tags in `src/crud_views/templatetags/crud_views.py`; theme leaves in `src/crud_views/templates/crud_views/tags/navbar.html`, `navbar_identity.html`, and `navbar_items.html`.
- Depends on: the completed request's view object, `_cv_ancestor_state` for descendant owner resolution, existing access/action admission helpers, and registered ViewSet routes. It does not create routes or query child collections.

**Extension apps:**
- Location: `src/crud_views_guardian/`, `src/crud_views_object_detail/`, `src/crud_views_workflow/`, `src/crud_views_polymorphic/`.
- Each has its own `apps.py`; workflow and guardian register checks in `checks.py` and workflow owns `models.py` + `migrations/`.

## Data Flow

### Primary Request Path

1. Consumer URLconf includes `viewset.urlpatterns` (`src/crud_views/lib/viewset/__init__.py:435`).
2. Django resolves to `view_class.as_view()`; class was registered by `CrudViewMetaClass`.
3. `CrudView.dispatch` consumes cancel-restore state, calls `_cv_ancestor_guard()` (no-op for top-level ViewSets; `_authorize_ancestors` otherwise), then Django `dispatch`; modal requests add `Vary: X-CV-Modal` (`src/crud_views/lib/view/base.py:326`).
4. `CrudViewPermissionRequiredMixin.dispatch`/`has_permission` evaluates the local permission derived from `ViewSet.permissions` and view key (`src/crud_views/lib/view/base.py:1223-1284`).
5. Handler builds context (`cv_get_context`, button/action data) and renders a theme template (`crud_views/view_*.html`), or the modal content template when `cv_modal` and `X-CV-Modal` are present.

### ViewSet Registration

1. `ViewSet(...)` validates (label modes, `verbose_name`, ancestor policy) and records the caller-supplied field names in `_manage_constructor_fields` for manage provenance.
2. `.register` (a property) rejects `resource_permissions` on model ViewSets, validates ancestor policy, derives `pk` from the model PK field type (or `Resource._meta.pk_type`), inserts into `_REGISTRY` under `_REGISTRY_LOCK` (duplicate name raises), then creates `AutoManageView` from `get_manage_view_class()` bound to the ViewSet (`src/crud_views/lib/viewset/__init__.py:183-217`). `GuardianViewSet` swaps the manage base to `GuardianManageView` *(inferred from baseline plus `src/crud_views_guardian/lib/viewset.py` class presence; override body not read)*.

### Nested Request Path

1. `ParentViewSet` supplies URL kwargs (`<parent>_pk`) and the FK attribute (`src/crud_views/lib/viewset/parentviewset.py`).
2. `urlpatterns` validates ancestor structure without relations (`_validate_ancestor_structure(self, relations=False)`); the request guard validates relations before lookup (`src/crud_views/lib/ancestors.py:124-149`).
3. `_authorize_ancestors` selects gates (`_selected_gates`), resolves each ancestor (`_resolve_ancestor`), applies provider-specific checks (model: `user.has_perm`; guardian: `_guardian_ancestor_has_permission`) and stores `_AncestorState`.
4. Child querysets are scoped (`_scope_child_queryset`) and objects verified (`_validate_child_parent`); `CreateViewParentMixin` sets the parent FK.

### Object Navbar Path

1. A consumer declares `NavBar(viewset=..., items=[NavItem(...)])` and mixes `CrudViewNavBarMixin` into only the views that should render it (`src/crud_views/lib/navbar.py`). The owner attachment must require an object; descendant attachments may be collection or object views.
2. `get_context_data()` places a request-view-owned `SimpleLazyObject` in `cv_navbar`; modal requests and views without a declaration get `None`. The navbar does no work until a rendering tag evaluates that value.
3. `_build()` resolves the owner from `view.object` on an owner page or `_resolved_ancestor(view, owner_name)` after the normal nested request guard has populated `_cv_ancestor_state` (`src/crud_views/lib/ancestors.py`). The same owner object supplies identity, access checks, state checks, and URL coordinates.
4. Each owner item targets a registered GET object view. Each child item targets a registered direct child collection view. Existing `cv_has_access` or `_cv_child_link_has_access` admission runs before `_cv_action_enabled_for_rendering`; denied or disabled items are omitted. Child-link admission only applies the existing destination/immediate-parent visibility policy; the destination request still runs the full ancestor guard and queryset scoping. URLs are reversed from ViewSet router names with current ancestor kwargs.
5. `{% cv_navbar %}` renders the configured wrapper or the active theme wrapper; `{% cv_navbar_identity %}` and `{% cv_navbar_items %}` render the shared lazy data through separate theme leaves. Modal requests and empty item lists emit no navbar markup. The default leaf templates provide plain identity and accessible section links (`aria-label`, `aria-current`).

The default theme contract is split into wrapper/identity/items leaves under `src/crud_views/templates/crud_views/tags/`. Theme selection comes from `CrudViewsSettings.theme_path` (`src/crud_views/lib/settings.py`); a custom wrapper can compose the two public leaf tags. A consumer template opts in by loading `crud_views` and placing `{% cv_navbar %}` in its chosen block (the independent demo uses `examples/bootstrap5/navbar_demo/templates/navbar_demo/crud_base.html`).

### Resource Request Path

1. Declare `class R(Resource)` with `Meta` and `cv_get_items`; `ViewSet(model=R, resource_permissions={...})`.
2. `ResourceViewMixin.get_queryset()`/`get_object()` call the loader hooks and report object lookup to the recorder (`src/crud_views/lib/resource.py`).
3. Manage page lists declared permission codenames and queries holders; it never calls the loader.

### Theme Data-API Prefix Path

1. `crud_views.lib.data_prefix` initializes `_data_prefix = "bs"`; themes call the public `crud_views.lib.register_data_prefix()` from `AppConfig.ready()`. Registration validates the token and replaces the process-wide scalar; the last valid startup call wins.
2. `cv_data_prefix()` in `src/crud_views/templatetags/crud_views.py` reads the current scalar at render time. The actions menu, language selector, vertical object-detail tabs, and accordion group templates use it for native toggle/target/parent/Popper attributes.
3. `cv_config` and `cv_const_js` pass the current scalar through inclusion context to `src/crud_views/templates/crud_views/tags/cv_config.html` as `data-data-prefix`.
4. The object-detail initializer in `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js` reads that attribute when selecting tab triggers inside `[data-cv-od-tabs]`. It does not select or replace the theme's tab adapter.

The prefix affects framework-owned data attributes and the owned-tabs selector only. It does not rename `data-cv-*` hooks or adapt host markup; structural differences still need template overrides.

### Breadcrumb and Table Rendering Paths

1. `CrudViewBreadcrumbMixin.get_context_data()` supplies `cv_breadcrumb`; the inclusion tag resolves its items (`src/crud_views/lib/breadcrumb.py`, `src/crud_views/templatetags/crud_views.py`). The stock leaf resolves list/item/active classes through `cv_button_class`, applying the active contribution and `aria-current="page"` only to the final item (`src/crud_views/templates/crud_views/tags/breadcrumb.html`).
2. django-tables2 configures effective ordering from request parameters or declared defaults. The stock header reads `column.orderable`, `column.is_ordered`, and `column.order_by_alias.is_descending`; orderable headers expose `ascending`, `descending`, or `none`, with icons only for ordered columns (`src/crud_views/templates/crud_views/table/bootstrap5.html`).
3. Sort links use `cv_querystring table.prefixed_order_by_field=column.order_by_alias.next`, preserving unrelated parameters. Non-orderable columns receive no generated sort attribute, icon or link. `tests/test1/test_table_template.py` covers request, constructor, `Meta.order_by`, prefixed tables, links and escaped attrs; `tests/test1/test_breadcrumb.py` covers default bytes, precedence, empty values and current-item semantics.

### Access Trace Path (cv_access, Phases 06.34 and 06.37)

1. `cv_access <path> <user>|--anonymous [--as-json] | --schema` (`src/crud_views/management/commands/cv_access.py`). `--schema` is exclusive, needs no actor, and prints `export_schema()` (exit via CommandError returncode 2 on bad combos).
2. `resolve_trace_user` (username first, then PK) -> `trace_access(path, actor)` -> `_run_trace` (`src/crud_views/lib/access_trace_runner.py:385`).
3. `_run_trace` runs inside `transaction.atomic(using="default")` with `set_rollback(True)`; resolves only `CrudView` routes (else `Resolver404` -> `no_such_route`); builds `_TraceRequest` (http://localhost, `_MemorySession`, `_MemoryMessages`); runs `_run_login_middleware`; instantiates the view, replaces `get` with `_handler_stub`, wraps custom methods (`_observe_custom_methods`, `_observe_denial_response`), computes `_plan_gates`, then `view.dispatch`.
4. Gates call `get_recorder().record(owner, kind, **facts)`; the recorder deduplicates identical reports per owner. Response is classified (`_classify_response`) into `allowed | denied | not_found | login_redirect | no_such_route | error`; `decided_by` points at the last terminal step.
5. The command calls `validate_export(trace.to_dict())` as a gate before rendering; failure raises `CommandError` (returncode 2) naming only the exception class and escaped locations, never input values. Valid traces keep their exact bytes.
6. Exit codes: allowed 0; denied/not_found/login_redirect 1; no_such_route/error 2.
7. The manage page can run the same engine (`ManageView.get_manage_access_trace`, modes `path` and `viewset`) when `CRUD_VIEWS_MANAGE_ACCESS_TRACE` is on; template `src/crud_views/templates/crud_views/includes/access_trace.html`.

### ViewSet Configuration CLI Path (cv_manage_view, Phase 06.36)

1. `cv_manage_view --list | --schema | <viewset> [<view>] [--user U] [--as-json]` (`src/crud_views/management/commands/cv_manage_view.py`). Invalid combinations yield a `failed` report with code `invalid_arguments`.
2. `_load_catalogue()` requires URLconf discovery (`_url_configuration_loaded()` from `src/crud_views/checks.py`) so lazily imported view modules have registered; it snapshots `_REGISTRY` under the lock, sorted by name.
3. `_inspect()` instantiates the ViewSet's `manage` view and, inside `manage.manage_export()`, calls the nine builders in fixed order: facts, presentation, views, routes, hierarchy, ancestor_policy, permissions, checks, guardian (guardian is `not_applicable` unless identity kind is `guardian`).
4. Each raw builder result passes through `adapt_section()` (`src/crud_views/lib/manage_report.py`), which validates against strict `WireModel`s. Collector exceptions become `status="error"` sections with code `collection_failed`; validation failures use `output_validation_failed`. Result status is `complete | partial | failed`.
5. `Report.validate_python()` validates the whole document, JSON is emitted with `ensure_ascii=True, allow_nan=False`. Exit codes: 0 ok; 1 when any check message level >= 40 (error); 2 for any non-complete report.
6. `report_schema()` (serialization mode) feeds `--schema`; the committed copy is `docs/reference/cv_manage_view.schema.json`, verified by `tests/check_manage_schema.py` and `tests/test1/test_manage_command*.py`.

### Bulk Selection and Execution Path

1. A table or card view opts in with `BulkSelectionMixin` and `cv_bulk_actions`; the mixin adds checkboxes and action submits while leaving ordinary list GET and POST behavior alone (`src/crud_views/lib/bulk/__init__.py`, `src/crud_views/templates/crud_views/snippets/bulk_toolbar.html`).
2. The action key must resolve in the same ViewSet to a `BulkFormViewPermissionRequired` subclass; system checks also validate model shape, action form and positive `cv_bulk_max` (`src/crud_views/lib/bulk/__init__.py`).
3. POST IDs are normalized using the model PK field. Review queries intersect the destination-visible queryset with the base ViewSet and nested-parent scope, then classify missing, unauthorized, ineligible and explicitly excluded rows without exposing inaccessible labels.
4. Confirmation posts eligible and blocked IDs back to the destination. Execution re-resolves and rechecks selection inside `cv_get_atomic()`, rejects changed eligibility, then invokes the consumer write through `cv_form_valid()` and its hook. A `cv_on_commit` callback runs after the transaction (`src/crud_views/lib/bulk/__init__.py`).
5. The example consumer demonstrates extension points and per-object checks in `examples/bootstrap5/bulk_selection/views.py`; list/card templates are `src/crud_views/templates/crud_views/view_list_table.content.html` and `view_card.content.html`.

## Key Abstractions

**ViewSet:**
- Purpose: collection registry, routing contract, permission metadata, per-collection presentation overrides.
- Examples: `src/crud_views/lib/viewset/__init__.py`, `src/crud_views_guardian/lib/viewset.py`.
- Pattern: Pydantic `BaseModel` with `PrivateAttr` state (`_views`, `_default_permissions`, `_manage_constructor_fields`); `_ancestor_provider` ClassVar (`"model"`, overridden by Guardian).

**CrudView:**
- Purpose: mixin contract shared by every package CBV.
- Pattern: `cv_viewset`, `cv_key`, `cv_path`, `cv_object` attributes; `cv_get_requirement()` returns `{"kind", "value", "ancestor_applies"}` describing the owning gate without evaluating it (consumed by manage).

**AncestorPolicy / AncestorPermissions:**
- Purpose: strict, stateless config (`provider`, `accept_global_perms`, `cascade`, `read`, `write`, `actions`).
- Examples: `src/crud_views/lib/ancestor_policy.py`; defaults mirrored by `CRUD_VIEWS_ANCESTOR_*` settings.

**Resource:**
- Purpose: Pydantic row type with `Meta` (verbose names, `app_label`, `pk_field`, `pk_type`, `ordering`) exposed through `ResourceOptions` as `_meta`.
- Constraint: `src/crud_views/lib/resource.py` is a leaf and must not import `crud_views.lib.viewset` (circular import).

**AccessRecorder / AccessTrace:**
- Purpose: scalar, versioned record of gates encountered in one attempt.
- Pattern: module-level `ContextVar` + `recording()` context manager; `_object_identity` stores only model label and PK string.

**Wire contracts (`WireModel`, `_TraceModel`):**
- Purpose: representation-only Pydantic models. `WireModel` in `src/crud_views/lib/manage_report.py` is `strict=True`, tolerates additive fields, `revalidate_instances="always"`. `_TraceModel` in `src/crud_views/lib/access_trace_export.py` uses the same options plus `extra="forbid"`.
- Pattern: `Section[T]` generic with a coherence validator (`ok` iff data present, `error` iff errors referenced); `CatalogueResult`/`InspectionResult` discriminated by `kind`; `version: Literal[1]`.
- Note: the access-trace `AccessTrace`/`AccessStep` dataclasses remain the Python API. The Pydantic export models are internal ("not a public Python API"). There is no module named `access_trace_contract`; the contract module is `access_trace_export.py`, tested by `tests/test1/test_access_trace_contract.py`.

**ManageView:**
- Purpose: developer-only page and data source for diagnostics.
- Pattern: gated by `_cv_manage_allowed` (authenticated, active, `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` mode, membership in `CRUD_VIEWS_MANAGE_GROUP`), reporting `manage_gate` steps. Builders return display values by default and complete typed metadata (`_export`, `SourceRecord`) when `manage_export()` is active.

**NavBar / NavItem:**
- Purpose: declarative, opt-in object navigation attached through `CrudViewNavBarMixin`.
- Pattern: `NavBar` names an owner ViewSet and ordered destinations; each `NavItem` targets one owner object-view key or a direct child collection ViewSet. `_build()` validates destinations, resolves the request's owner, applies existing admission/state checks, reverses registered router names, then determines the active direct-child section (`src/crud_views/lib/navbar.py`).
- Constraint: context carries a request-instance `SimpleLazyObject`; the first theme tag evaluates it. Do not eagerly build navigation in `get_context_data()` or cache it on the declaration/ViewSet.

## Entry Points

**App initialization:** `src/crud_views/apps.py` (`ready()` imports `crud_views.checks`); extension `apps.py` files.
**Theme data-prefix initialization:** theme `AppConfig.ready()` calls `crud_views.lib.register_data_prefix()`; default scalar is initialized in `src/crud_views/lib/data_prefix.py`.
**URL generation:** `ViewSet.urlpatterns` in `src/crud_views/lib/viewset/__init__.py`.
**Object navigation:** `CrudViewNavBarMixin` in `src/crud_views/lib/navbar.py`; render through `{% cv_navbar %}`, `{% cv_navbar_identity %}`, `{% cv_navbar_items %}` in `src/crud_views/templatetags/crud_views.py`.
**Management commands:** `cv_access`, `cv_manage_view`, `cv_manage_group`, `cv_assets`, `crud_views_show` (placeholder, prints nothing) in `src/crud_views/management/commands/`.
**Manage page:** auto-registered `AutoManageView` per ViewSet; trace form via `ManageView.get_manage_access_trace`.
**Template tags:** `{% load crud_views %}` in `src/crud_views/templatetags/crud_views.py`.

## Architectural Constraints

- **Theme class state:** `register_button_classes()` merges into process-wide `_THEME_BUTTON_CLASSES` and resets resolved-class caches; project setting changes invalidate the cache too (`src/crud_views/lib/button_classes.py`). Use this registry for breadcrumb styling.
- **Header attribute ownership:** the stock header owns `aria-sort`. Caller-supplied same-name attrs are unsupported: remove them or override `table.thead`; no collision deduplication is promised (`src/crud_views/templates/crud_views/table/bootstrap5.html`, `docs/reference/list_view.md`).

- **Threading/context:** `_REGISTRY` is module-level guarded by `_REGISTRY_LOCK` (`threading.Lock`); recorder state is a `ContextVar` (`src/crud_views/lib/access_trace.py`). `ViewSet.default_permissions` caches per process once non-empty (#151 comment in code).
- **Import-time registration:** view classes register when their module is imported; URLconf discovery must have completed before the registry is complete, which is why `cv_manage_view` and some checks call `_url_configuration_loaded()` (`src/crud_views/checks.py`).
- **Theme prefix lifecycle:** `register_data_prefix()` mutates one process-wide scalar and is intended for app startup, not request-local or concurrent tenant/theme switching. Tags and config contexts read it when called/rendered (`src/crud_views/lib/data_prefix.py`, `src/crud_views/templatetags/crud_views.py`).
- **Database effects of traces:** `cv_access` runs in a rolled-back transaction on `default` only; custom gates may still cause other side effects (no general sandbox).
- **Trace scope:** synthetic GET to `http://localhost`; handler-phase checks, other middleware and decorators not reproduced; recorded under `untraced` in the output.
- **Pydantic compatibility:** wire modules deliberately use `typing_extensions.TypeAliasType`, `Generic[...]` instead of PEP 695 syntax and validation-mode schema for the trace, noted in comments as Pydantic 2.2 compatibility (`src/crud_views/lib/manage_report.py`, `src/crud_views/lib/access_trace_export.py`).
- **Contracts import before Django:** `access_trace.py` and `access_trace_export.py` document being importable before Django configuration.
- **Resource boundary:** Resources are never parents; model ancestors resolve first; nested filtering belongs in the app loader (`src/crud_views/lib/resource.py`, `src/crud_views/lib/ancestors.py`).
- **Bulk action boundary:** bulk forms require scalar-PK ORM models and querysets on the default database; do not assume they support Resource rows, composite identifiers, or multi-database writes (`src/crud_views/lib/bulk/__init__.py`). Put the domain mutation in `cv_form_valid()` and keep object eligibility in `cv_bulk_check()`/`cv_bulk_has_permission()`.
- **Guardian:** replaces the ViewSet class and manage view; does not support Resource models.
- **Package layout:** distribution ships five apps from `src/`; optional apps must not be imported by core modules.

## Anti-Patterns

### Deriving table sort presentation from raw query parameters
**What happens:** a copied header decides its icon or `aria-sort` from a literal `sort` parameter.
**Why it's wrong:** it misses constructor/default ordering and prefixed table parameters.
**Do this instead:** read bound-column state and use `table.prefixed_order_by_field` for links, following `src/crud_views/templates/crud_views/table/bootstrap5.html`; verify with `tests/test1/test_table_template.py`.

### Reimplementing sibling route construction
**What happens:** hand-built URLs or reverse names.
**Why it's wrong:** loses PK converters, parent kwargs and `cv_path_contribute()` extras.
**Do this instead:** `ViewSet.get_router_name`, `CrudView.cv_get_url`/`cv_get_router_and_args` (`src/crud_views/lib/view/base.py`).

### Duplicating authorization in diagnostics
**What happens:** a diagnostic guesses permissions itself.
**Why it's wrong:** diverges from provider, ancestor, object and custom gates.
**Do this instead:** record at the owning gate with `get_recorder()`; label unobserved behavior as a limitation (`_add_limitations` in `src/crud_views/lib/access_trace_runner.py`).

### Running the real handler during a trace
**What happens:** executing list/detail/form logic to decide access.
**Why it's wrong:** business logic, cost or writes.
**Do this instead:** keep `_handler_stub` and the rollback transaction.

### Emitting hand-built report dicts
**What happens:** a builder or command writes JSON without passing through the wire models.
**Why it's wrong:** consumers rely on strict, versioned shapes.
**Do this instead:** route new sections through `adapt_section` and the `Report` TypeAdapter (`src/crud_views/lib/manage_report.py`); add trace fields to `Step`/`PlanRow` in `src/crud_views/lib/access_trace_export.py` alongside `AccessStep`; changing shapes requires bumping `version` and regenerating `docs/reference/cv_manage_view.schema.json`.

### Importing viewset from Resource
**What happens:** `crud_views.lib.resource` imports anything under `crud_views.lib.viewset`.
**Why it's wrong:** circular import when `resource` is imported first.
**Do this instead:** inline constants (see `ResourceMeta.pk_type`).

## Error Handling

**Strategy:** Django 403/404/redirect for requests; `cv_raise` / package exceptions (`src/crud_views/lib/exceptions.py`) for invalid declarations; structured outcomes for diagnostics.

**Patterns:**
- Ancestor misconfiguration raises `_AncestryError(ImproperlyConfigured)` with a `kind` (`src/crud_views/lib/ancestors.py:80`).
- `cv_manage_view` never raises per collector: it records `ReportError` (`code`, `section`, `message`, `exception_class`, `location`) and degrades `complete -> partial -> failed`.
- `cv_access` raises `CommandError(returncode=2)` for usage and output-validation errors; outcomes map to exit codes in `handle`.
- Trace steps keep exception class/message as scalar `{"class","message"}`.

## Cross-Cutting Concerns

**Logging:** none imposed; Django/consumer configuration.
**Validation:** ViewSet Pydantic validators; `Check` hierarchy in `src/crud_views/lib/check.py` (`CheckAttribute`, `CheckTemplate`, `CheckExpression`, `CheckUnknownAttributes`, ...) returned from `CrudView.checks()`/`ViewSet.checks()`; Django checks in `src/crud_views/checks.py` (`check_viewsets`, `check_ancestor_declarations`, `check_conditional`, `check_ordered_model_installed`, `check_asset_registry`, `check_asset_pipeline`, plus settings messages); settings messages from `CrudViewsSettings.check_messages`.
**Settings:** `crud_views_settings` singleton (`src/crud_views/lib/settings.py`): manage mode/group/show-users/access-trace/view-class, theme (`theme_path`, templates under `crud_views/`), session key, origin param (`cv_from`), CSP nonce attr, asset bundling, inaccessible actions (`hide|disable`), inline/label-mode action settings, ancestor cascade/read/write defaults, breadcrumb prefix, filter persistence/pinned, per-view default action lists, delete preview limit.
**Assets:** `register_assets(key, js, css, emit)` stores `AssetBundle`s (`src/crud_views/lib/assets.py`); `cv_css`/`cv_js` render them with optional CSP nonce and SRI; `cv_sources` (`src/crud_views/lib/pipeline.py`) bundles them for django-pipeline; `cv_assets` command lists delivery.
**Authentication:** Django auth locally; ancestors via `ancestors.py`; per-object via Guardian.
**Runtime CLI contracts:** `cv_manage_view` and `cv_access` are independent management-command interfaces. Their versioned Pydantic output boundaries live in `src/crud_views/lib/manage_report.py` and `src/crud_views/lib/access_trace_export.py`; command parsing/rendering/exit codes stay in `src/crud_views/management/commands/`.
**i18n:** gettext in package code, locale `de` under each `locale/` directory (`src/crud_views/locale/de/LC_MESSAGES/django.po`).

---

*Architecture analysis: 2026-11-21*
