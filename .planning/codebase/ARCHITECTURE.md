---
last_mapped_commit: 597d086f3e1e5d418a39b2def8af39cfcbbd8420
last_mapped_at: 2026-11-25
---
<!-- refreshed: 2026-11-25 -->
# Architecture

**Analysis Date:** 2026-11-25

Scope: reusable apps under `src/`, consumer examples under `examples/bootstrap5/`, diagnostic contracts, theme registration and bulk rendering. Follow the developer-maintainability constraint in `AGENTS.md`: prefer bounded opt-in additions, keep behavior traceable, and avoid hidden state or added queries on existing request paths.

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
| Private link-access evaluator | Link-only parent/own permission then action-state evaluation; consumes caller-supplied objects and does not authorize requests or resolve/store decisions | `src/crud_views/lib/link_access.py` |
| Concrete views | `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`, `ActionView`, `OrderedUp/DownView`, `CardListView`, `CustomFormView`, `CustomFormNoObjectView`, `RedirectChildView`, each with `*PermissionRequired` | `src/crud_views/lib/views/` |
| View mixins | `CrudViewProcessFormMixin`, `MessageMixin`, `CardOrderMixin`, `ListViewTableMixin`, `ListViewTableFilterMixin` | `src/crud_views/lib/views/mixins.py` |
| Action/button projection | Buttons, button data, action menus, label modes, visibility, cancel target | `src/crud_views/lib/view/buttons.py`, `button_data.py`, `action_menu.py`, `label_mode.py`, `visibility.py`, `cancel.py` |
| Ancestor engine | Walk/validate parent chain, authorize ancestors per request, scope child queryset | `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/ancestor_policy.py`, `src/crud_views/lib/ancestor_db.py` |
| `Resource` / `ResourceViewMixin` | Non-ORM rows via `cv_get_items`/`cv_get_item`; `_meta` duck type (`ResourceOptions`) | `src/crud_views/lib/resource.py` |
| Bulk selection and action form | Opt-in table/card selection plus permission-gated review and transactional execution of selected ORM objects | `src/crud_views/lib/bulk/__init__.py` |
| Bulk toolbar button boundary | Normalize native submit payloads through the form contract, attach the destination semantic variant, then render the dedicated bulk leaf | `src/crud_views/lib/bulk/__init__.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views/templates/crud_views/tags/button/bulk.html` |
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
| Theme CSS tokens | Six opt-in `--cv-*` custom-property reads with Bootstrap and literal fallbacks; manage palette and formset surfaces stay themeable without upstream declarations | `src/crud_views/static/crud_views/css/manage.css`, `src/crud_views/static/crud_views/css/formset.css`, `docs/reference/theme.md` |
| Compact formset gutters | Bootstrap `gx-3` utility on the shared headings row and crispy-generated field row; component hooks remain for layout behavior | `src/crud_views/templates/crud_views/formsets/compact_headings.html`, `src/crud_views/lib/formsets/compact.py` |
| Template tags | `cv_css`, `cv_js`, `cv_config`, action/button/context tags, formset tag | `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templatetags/crud_views_formsets.py` |
| Native data-API prefix | Startup-registered scalar (default `bs`); read by rendering tags, config context, theme templates, and object-detail tab selector | `src/crud_views/lib/data_prefix.py`, `src/crud_views/lib/__init__.py`, `src/crud_views/templatetags/crud_views.py` |
| JavaScript theme config | Startup namespace and per-location tooltip defaults; copied into the rendered `#cv-config` element for browser-side adapter selection | `src/crud_views/lib/js_config.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/tags/cv_config.html` |
| JavaScript UI adapters | Late-resolved compatible global namespace and replaceable `cv.adapters` interface for modal, tooltip, tab, collapse, and alert behavior | `src/crud_views/static/crud_views/js/adapters.js` |
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
- Request authorization remains `dispatch()` -> `_cv_ancestor_guard()` -> Django permission mixin / local `has_permission()` and state check. `src/crud_views/lib/link_access.py` is a separate presentation-time evaluator; it does not replace or weaken this request path.

**Link access and action projection:**
- Purpose: decide destination visibility and state using caller-supplied own objects and known ancestry.
- Location: `src/crud_views/lib/link_access.py`; consumers are `src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/card.py`, `src/crud_views/lib/navbar.py`, `src/crud_views/lib/bulk/__init__.py`, and `src/crud_views/templatetags/crud_views.py`.
- `_known_link_ancestors()` aligns objects to the target's declared chain using request-resolved state. Child links explicitly supply their URL parent. Explicit `None` remains unknown; no relation access or query fills an unknown level. Missing immediate parents deny every nested target; unknown higher ancestors are skipped (`src/crud_views/lib/link_access.py`).
- `_link_permission()` checks supplied higher ancestors outermost first, then the target's private `_cv_link_permission()` seam checks the immediate parent and own permission. `_link_access()` runs state only after permission passes. State receives own object for object views, immediate parent for nested non-object views, otherwise `None`. `_link_ctx()` preserves the existing permission/state visibility fields.
- Guardian nested-create links require an active authenticated actor and passing declared higher/immediate gates before `cv_create_has_access(user, rendering_view, parent_obj)`. A custom override cannot bypass those gates. The default hook repeats its bounded immediate-parent check. Nested-create `cv_has_access()` returns false and is not called by that link path (`src/crud_views_guardian/lib/views.py`).
- Actual link destinations drive checks. Public `cv_has_access()` receives only a destination's own object or `None`; page objects and parents are separate inputs. Shared link checks neither authorize requests nor cache final decisions (`src/crud_views/lib/view/base.py`, `src/crud_views/lib/link_access.py`).

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
- Toolbar styling: `BulkSelectionMixin.cv_bulk_buttons` normalizes with `cv_button_data(raw, "form")`, applies `destination.cv_action_variant` (an unset `None`/`""` value renders as `bulk:secondary`), and renders `src/crud_views/templates/crud_views/tags/button/bulk.html`. `bulk` is a class-registry and label-mode location, not a generic action-normalization location. Both `cv_button_data(..., "bulk")` and `{% cv_button location="bulk" %}` raise `ValueError` (`src/crud_views/lib/view/button_data.py`, `src/crud_views/templatetags/crud_views.py`).
- Offering: `BulkSelectionMixin` offers an action only when its destination view passes `cv_has_access` and `cv_action_enabled` for the viewer (request-local cached `_cv_effective_bulk_actions`/`cv_bulk_buttons`). With nothing offered, no toolbar and no selection checkboxes render; `snippets/bulk_toolbar.html` guards itself. `cv_bulk_buttons` is evaluated in `get_context_data` so presentation errors surface instead of being swallowed by templates. Submission enforcement at the destination is unchanged.
- Theme classes: `bulk:primary`, `bulk:secondary`, `bulk:tertiary`, and `bulk:danger` all default to `btn btn-primary`; mode-specific keys take precedence, including empty/None overrides. The leaf retains form tooltip, hidden-label and host-icon semantics; review Confirm still uses `form:submit` (`src/crud_views/lib/button_classes.py`, `src/crud_views/templates/crud_views/tags/button/bulk.html`).

**Diagnostics (manage + trace + CLI contracts):**
- Purpose: developer-facing projections of configuration and access.
- Location: `src/crud_views/lib/views/manage.py`, `src/crud_views/lib/manage_report.py`, `src/crud_views/lib/access_trace*.py`, `src/crud_views/management/commands/`.

**Presentation and support:**
- Purpose: forms, tables, formsets, conditional fields, action rendering, assets.
- Location: `src/crud_views/lib/{crispy,table,formsets,conditional}/`, `src/crud_views/lib/{breadcrumb,icons,messages,session,deletion,ordered}.py`, `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/`.

**Theme styling contract:**
- Purpose: keep theme-specific palette adaptation declarative while retaining usable stock styling when tokens are not mapped.
- Location: manage consumers in `src/crud_views/static/crud_views/css/manage.css`; formset cards, compact rows, and nested child surfaces in `src/crud_views/static/crud_views/css/formset.css`; published contract in `docs/reference/theme.md`.
- The six consumed properties are `--cv-secondary-color`, `--cv-secondary-text-emphasis`, `--cv-body-bg`, `--cv-border-color`, `--cv-border-radius`, and `--cv-tertiary-bg`. Each use falls back through its matching Bootstrap property to a literal value; upstream does not declare these tokens on `:root`.
- Themes should map all six properties on each theme root so nested color modes resolve against their local theme variables. Keep the fallback chain at each use site. The manage help button retains its stock selector and assigns the token chain to Bootstrap's `--bs-btn-color` variable.
- Compact shared heading and field rows use `gx-3` in `src/crud_views/templates/crud_views/formsets/compact_headings.html` and `src/crud_views/lib/formsets/compact.py`; preserve both the utility and existing `cv-formset-*` hooks. The documented 1rem gutter equivalence assumes Bootstrap's standard spacing scale.

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
3. Permission-required compositions enter `CrudViewPermissionRequiredMixin.dispatch` first: the ancestor guard precedes Django's local permission and state checks. Plain `CrudView.dispatch` also guards the handler; successful request-local ancestor state prevents repeated authorization (`src/crud_views/lib/view/base.py:1246`, `src/crud_views/lib/view/base.py:1307`).
4. `CrudView.dispatch` consumes cancel-restore state and delegates to the Django handler after its guard; modal-capable responses add `Vary: X-CV-Modal`. Guardian object/queryset/parent mixins supply enforcing gates through the MRO (`src/crud_views/lib/view/base.py:331`, `src/crud_views_guardian/lib/mixins.py`).
5. Handler builds context (`cv_get_context`, button/action data) and renders a theme template (`crud_views/view_*.html`), or the modal content template when `cv_modal` and `X-CV-Modal` are present.

### ViewSet Registration

1. `ViewSet(...)` validates (label modes, `verbose_name`, ancestor policy) and records the caller-supplied field names in `_manage_constructor_fields` for manage provenance (`src/crud_views/lib/viewset/__init__.py`).
2. `.register` is a Pydantic `@model_validator(mode="after")`: it rejects `resource_permissions` on model ViewSets, validates ancestor policy, derives `pk` from the model PK field type (or `Resource._meta.pk_type`), inserts into `_REGISTRY` under `_REGISTRY_LOCK` (duplicate name raises), then creates `AutoManageView` from `get_manage_view_class()` bound to the ViewSet (`src/crud_views/lib/viewset/__init__.py:183`). `GuardianViewSet.register()` rejects Resources, calls the base registration, removes the generated manage entry and regenerates it through its override. `get_manage_view_class()` selects a configured class or `GuardianManageView` (`src/crud_views_guardian/lib/viewset.py:93`).

### Nested Request Path

1. `ParentViewSet` supplies URL kwargs (`<parent>_pk`) and the FK attribute (`src/crud_views/lib/viewset/parentviewset.py`).
2. `urlpatterns` validates ancestor structure without relations (`_validate_ancestor_structure(self, relations=False)`); the request guard validates relations before lookup (`src/crud_views/lib/ancestors.py:124-149`).
3. `_authorize_ancestors` selects gates (`_selected_gates`), resolves each ancestor (`_resolve_ancestor`), applies provider-specific checks (model: `user.has_perm`; guardian: `_guardian_ancestor_has_permission`) and stores `_AncestorState`.
4. Child querysets are scoped (`_scope_child_queryset`) and objects verified (`_validate_child_parent`); `CreateViewParentMixin` sets the parent FK.

### Link Access Path

1. Resolve the actual registered destination; pass its own object or `None`, separately from ancestry (`src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/card.py`).
2. Build the known chain with `_known_link_ancestors()`. Child controls supply their actual parent; sibling controls reuse resolved route ancestry. Same-ViewSet consumers supply the real rendering view to the permission hook; cross-ViewSet consumers supply `None` (`src/crud_views/lib/link_access.py`).
3. `_link_access()` performs known higher gates, immediate gate, own permission, then state. Permission filters call `_link_permission()` and deliberately omit state. Bulk source actions and navbar items require the full allowed result (`src/crud_views/templatetags/crud_views.py`, `src/crud_views/lib/bulk/__init__.py`, `src/crud_views/lib/navbar.py`).
4. Producers retain their own visibility, URL and template handling. Clicking enters the target's independent request guard, own permission and state path (`src/crud_views/lib/view/base.py`).

### Cancel Navigation Path

1. `cv_get_cancel_url()` binds any request override to a shallow view copy, reads the signed origin/query state and tests an eligible sibling origin before the configured fallback. Availability is memoized per destination only within that call (`src/crud_views/lib/view/base.py`).
2. Tokens are bounded, versioned, signed navigation transport bound to ViewSet identity and parent coordinates. They confer no permission; only eligible list destinations restore captured query state (`src/crud_views/lib/view/cancel.py`).
3. For nested targets, `_cancel_target_available()` obtains the immediate parent through `_cv_cancel_parent_object()`, then supplies it and already-known higher ancestors to the shared link check. The built-in missing-row `Http404` makes a target unavailable; application-hook exceptions, missing kwargs and database errors propagate (`src/crud_views/lib/view/base.py`).
4. Guardian object/list/create targets delegate through shared checks after actor admission. Parent-only non-create Cancel deliberately omits `cv_has_access()`: it checks composition, actor, known higher gates, immediate-parent access and state with the parent. Ordinary links retain their own-permission step (`src/crud_views_guardian/lib/mixins.py`).
5. An unavailable origin falls back; an unusable configured fallback raises `ImproperlyConfigured`; a valid fallback denied by access/state returns `None` (`src/crud_views/lib/view/base.py`).

### Object Navbar Path

1. A consumer declares `NavBar(viewset=..., items=[NavItem(...)])` and mixes `CrudViewNavBarMixin` into only the views that should render it (`src/crud_views/lib/navbar.py`). The owner attachment must require an object; descendant attachments may be collection or object views.
2. `get_context_data()` places a request-view-owned `SimpleLazyObject` in `cv_navbar`; modal requests and views without a declaration get `None`. The navbar does no work until a rendering tag evaluates that value.
3. `_build()` resolves the owner from `view.object` on an owner page or `_resolved_ancestor(view, owner_name)` after the normal nested request guard has populated `_cv_ancestor_state` (`src/crud_views/lib/ancestors.py`). The same owner object supplies identity, access checks, state checks, and URL coordinates.
4. Owner items target registered GET object views; child items target registered direct-child GET collection views. Both call the shared full link evaluator with aligned known ancestry. Owner items pass the owner as the own object; child items pass it as the immediate parent. Denied/disabled items are omitted. URLs use registered routes and current ancestor kwargs (`src/crud_views/lib/navbar.py`).
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

### Access Trace Path (cv_access)

1. `cv_access <path> <user>|--anonymous [--as-json] | --schema` (`src/crud_views/management/commands/cv_access.py`). `--schema` is exclusive, needs no actor, and prints `export_schema()` (exit via CommandError returncode 2 on bad combos).
2. `resolve_trace_user` (username first, then PK) -> `trace_access(path, actor)` -> `_run_trace` (`src/crud_views/lib/access_trace_runner.py:385`).
3. `_run_trace` runs inside `transaction.atomic(using="default")` with `set_rollback(True)`; resolves only `CrudView` routes (else `Resolver404` -> `no_such_route`); builds `_TraceRequest` (http://localhost, `_MemorySession`, `_MemoryMessages`); runs `_run_login_middleware`; instantiates the view, replaces `get` with `_handler_stub`, wraps custom methods (`_observe_custom_methods`, `_observe_denial_response`), computes `_plan_gates`, then `view.dispatch`.
4. Gates call `get_recorder().record(owner, kind, **facts)`; the recorder deduplicates identical reports per owner. Response is classified (`_classify_response`) into `allowed | denied | not_found | login_redirect | no_such_route | error`; `decided_by` points at the last terminal step.
5. The command calls `validate_export(trace.to_dict())` as a gate before rendering; failure raises `CommandError` (returncode 2) naming only the exception class and escaped locations, never input values. Valid traces keep their exact bytes.
6. Exit codes: allowed 0; denied/not_found/login_redirect 1; no_such_route/error 2.
7. The manage page can run the same engine (`ManageView.get_manage_access_trace`, modes `path` and `viewset`) when `CRUD_VIEWS_MANAGE_ACCESS_TRACE` is on; template `src/crud_views/templates/crud_views/includes/access_trace.html`.

### ViewSet Configuration CLI Path (cv_manage_view)

1. `cv_manage_view --list | --schema | <viewset> [<view>] [--user U] [--as-json]` (`src/crud_views/management/commands/cv_manage_view.py`). Invalid combinations yield a `failed` report with code `invalid_arguments`.
2. `_load_catalogue()` requires URLconf discovery (`_url_configuration_loaded()` from `src/crud_views/checks.py`) so lazily imported view modules have registered; it snapshots `_REGISTRY` under the lock, sorted by name.
3. `_inspect()` instantiates the ViewSet's `manage` view and, inside `manage.manage_export()`, calls the nine builders in fixed order: facts, presentation, views, routes, hierarchy, ancestor_policy, permissions, checks, guardian (guardian is `not_applicable` unless identity kind is `guardian`).
4. Each raw builder result passes through `adapt_section()` (`src/crud_views/lib/manage_report.py`), which validates against strict `WireModel`s. Collector exceptions become `status="error"` sections with code `collection_failed`; validation failures use `output_validation_failed`. Result status is `complete | partial | failed`.
5. `Report.validate_python()` validates the whole document, JSON is emitted with `ensure_ascii=True, allow_nan=False`. Exit codes: 0 ok; 1 when any check message level >= 40 (error); 2 for any non-complete report.
6. `report_schema()` (serialization mode) feeds `--schema`; the committed copy is `docs/reference/cv_manage_view.schema.json`, verified by `tests/check_manage_schema.py` and `tests/test1/test_manage_command*.py`.

### Bulk Selection and Execution Path

1. A table or card view opts in with `BulkSelectionMixin` and `cv_bulk_actions`; the mixin adds checkboxes and action submits only for destinations the viewer may enter, while leaving ordinary list GET and POST behavior alone (`src/crud_views/lib/bulk/__init__.py`, `src/crud_views/templates/crud_views/snippets/bulk_toolbar.html`).
2. The action key must resolve in the same ViewSet to a `BulkFormViewPermissionRequired` subclass; system checks also validate model shape, action form and positive `cv_bulk_max` (`src/crud_views/lib/bulk/__init__.py`).
3. The destination validates exactly one stage and counts raw candidate plus excluded entries before normalization, enforcing `cv_bulk_max` (default 100). `_read_ids()` converts with the model PK field, stringifies and deduplicates in submission order; empty/NUL/invalid IDs and overlap between normalized candidate/excluded lists cause `BadRequest`. Review queries intersect the destination-visible queryset with the base ViewSet and nested-parent scope, then classify missing, unauthorized, ineligible and explicitly excluded rows without exposing inaccessible labels (`src/crud_views/lib/bulk/__init__.py:184`).
4. Confirmation posts eligible and blocked IDs back to the destination. Execution re-resolves and rechecks selection inside `cv_get_atomic()`, rejects changed eligibility, then invokes the consumer write through `cv_form_valid()` and its hook. A `cv_on_commit` callback runs after the transaction (`src/crud_views/lib/bulk/__init__.py`).
5. The example consumer demonstrates extension points and per-object checks in `examples/bootstrap5/bulk_selection/views.py`; list/card templates are `src/crud_views/templates/crud_views/view_list_table.content.html` and `view_card.content.html`.
6. Source controls use a separate presentation pipeline: take the bulk label-mode floor (fallback to label when the icon is unavailable), normalize form data, attach the destination variant and render `src/crud_views/templates/crud_views/tags/button/bulk.html`. Native `name="cv_bulk_stage"`, `value="review"` and destination `formaction` remain functional without JavaScript. Review hidden IDs and card checkbox values use `unlocalize` so numeric PK transport remains machine-readable (`src/crud_views/templates/crud_views/view_bulk_form.content.html`, `src/crud_views/templates/crud_views/view_card.content.html`).

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
**JavaScript theme configuration:** theme `AppConfig.ready()` can call `register_js_namespace()` and `register_tooltip_placements()` exported from `src/crud_views/lib/__init__.py`; the state lives in `src/crud_views/lib/js_config.py` and is read when `{% cv_config %}` / `{% cv_const_js %}` renders.
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

### Sending bulk toolbar payloads through the action normalizer
**What happens:** a consumer passes `location="bulk"` to `cv_button_data()` or `cv_button`, or changes global `form:submit` classes to style toolbar destinations.
**Why it's wrong:** bulk controls have a dedicated native-submit contract; both generic entry points reject the bulk location. Toolbar class selection belongs to destination variants rather than the form submit class.
**Do this instead:** follow `BulkSelectionMixin.cv_bulk_buttons` in `src/crud_views/lib/bulk/__init__.py`: normalize with the form location and effective bulk label mode, then add the destination variant and render `src/crud_views/templates/crud_views/tags/button/bulk.html`. Theme overrides belong to `bulk:<variant>[:<mode>]` in `src/crud_views/lib/button_classes.py`.

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

**Logging:** Python module loggers use the consumer's Django logging configuration, including non-strict button-normalization diagnostics in `src/crud_views/lib/view/button_data.py`.
**Validation:** ViewSet Pydantic validators; `Check` hierarchy in `src/crud_views/lib/check.py` (`CheckAttribute`, `CheckTemplate`, `CheckExpression`, `CheckUnknownAttributes`, ...) returned from `CrudView.checks()`/`ViewSet.checks()`; Django checks in `src/crud_views/checks.py` (`check_viewsets`, `check_ancestor_declarations`, `check_conditional`, `check_ordered_model_installed`, `check_asset_registry`, `check_asset_pipeline`, plus settings messages); settings messages from `CrudViewsSettings.check_messages`.
**Settings:** `crud_views_settings` singleton (`src/crud_views/lib/settings.py`): manage mode/group/show-users/access-trace/view-class, theme (`theme_path`, templates under `crud_views/`), session key, origin param (`cv_from`), CSP nonce attr, asset bundling, inaccessible actions (`hide|disable`), inline/label-mode action settings, ancestor cascade/read/write defaults, breadcrumb prefix, filter persistence/pinned, per-view default action lists, delete preview limit.
**Assets:** `register_assets(key, js, css, emit)` stores `AssetBundle`s (`src/crud_views/lib/assets.py`); `cv_css`/`cv_js` render them with optional CSP nonce and SRI; `cv_sources` (`src/crud_views/lib/pipeline.py`) bundles them for django-pipeline; `cv_assets` command lists delivery.
**Browser configuration and adapters:** `src/crud_views/lib/js_config.py` owns process-wide theme defaults: a single validated JavaScript global identifier (default `bootstrap`, last valid registration wins) and a copied, whole-map tooltip placement setting (default `{}`). Both template tags call `_cv_config_context()` at render time, which also supplies request path/query, CSRF token, and the independent native data prefix; the default `src/crud_views/templates/crud_views/tags/cv_config.html` serializes these as escaped `data-*` attributes on hidden `#cv-config` and includes the modal shell. `src/crud_views/static/crud_views/js/adapters.js` reads that node when each adapter operation needs the UI namespace and builds Bootstrap-compatible modal, tooltip, tab, collapse, and alert defaults. Core scripts dispatch through `cv.adapters` at call time; themes may replace entries. The stock modal adapter listens to `hide.{prefix}.modal` / `hidden.{prefix}.modal`, where `{prefix}` is the registered data prefix read from `#cv-config` `data-data-prefix` (default `bs`), rather than fixed `*.bs.modal` events; its missing-component error does not name Bootstrap. The stock tooltip adapter reads the placement map and native prefix at initialization time, and an explicit `data-{prefix}-placement` on a trigger takes precedence. Keep the namespace, tooltip map, and data prefix independently registered; absent legacy attributes use `bootstrap`, `{}`, and `bs` respectively. Theme startup examples and lifecycle constraints are in `docs/reference/theme.md` and `docs/reference/javascript.md`.
**Theme CSS:** six `--cv-*` palette/shape tokens are consumed by `manage.css` and `formset.css` with Bootstrap-property and literal fallbacks; themes own mappings on their theme roots (`docs/reference/theme.md`). Compact headings and fields add the Bootstrap `gx-3` utility at their respective template/helper row declarations.
**Authentication:** Django auth locally; ancestors via `ancestors.py`; per-object via Guardian.
**Runtime CLI contracts:** `cv_manage_view` and `cv_access` are independent management-command interfaces. Their versioned Pydantic output boundaries live in `src/crud_views/lib/manage_report.py` and `src/crud_views/lib/access_trace_export.py`; command parsing/rendering/exit codes stay in `src/crud_views/management/commands/`.
**i18n:** gettext in package code, locale `de` under each `locale/` directory (`src/crud_views/locale/de/LC_MESSAGES/django.po`).

## Guardian Grant Reuse Path

1. Own-object request checks and callable destination checks in `src/crud_views_guardian/lib/mixins.py` preserve actor, permission and fallback gates before calling `_get_guardian_checker(user)`.
2. `src/crud_views_guardian/lib/permissions.py` acquires one `ObjectPermissionChecker` through the private `_cv_guardian_checker` attribute on that Python user; the import remains optional and lazy.
3. `src/crud_views_guardian/lib/ancestors.py::_request_checker(view, user)` delegates to the same helper. The view argument is a test seam; the user object owns the checker.
4. Guardian reuses loaded grants for matching model/object identities. Destination permission membership and action-state evaluation remain independent; no final access answer is stored by the helper.
5. Normal middleware requests provide fresh user/checker ownership. A user retained beyond its request retains loaded grants, including stale additions/revocations. The workflow permission-refusal reload can therefore render its error once with retained grants; the next normal request observes revocation (`src/crud_views_workflow/lib/views.py`, `tests/test1/test_workflow_review.py`).

This is a bounded change to existing Guardian acquisition sites. It adds no global registry, prefetch operation, cross-request cache service or public refresh API. Backend/queryset permission paths remain independent.

---

*Architecture analysis: 2026-11-25*
