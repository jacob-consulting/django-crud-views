---
last_mapped_commit: 38b0100683fa71412b8bc00dd0eeb7f985efb459
last_mapped_at: 2026-10-25
---
<!-- refreshed: 2026-10-25 -->

# Architecture

**Analysis Date:** 2026-10-25

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                     Host Django project (consumer code)                       │
│   views.py: ViewSet(...) + CrudView subclasses   urls.py: vs.urlpatterns     │
│   e.g. `examples/bootstrap5/library/views.py`, `tests/test1/app/views.py`     │
└───────────────┬──────────────────────────────────────────────┬───────────────┘
                │ class definition (metaclass registers)       │ URL resolve
                ▼                                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     Registry / Routing layer                                  │
│  ViewSet (Pydantic) `src/crud_views/lib/viewset/__init__.py`                  │
│  ParentViewSet      `src/crud_views/lib/viewset/parentviewset.py`             │
│  PK regexes         `src/crud_views/lib/viewset/path_regs.py`                 │
│  CrudViewMetaClass  `src/crud_views/lib/view/meta.py`                         │
└───────────────┬──────────────────────────────────────────────────────────────┘
                │ as_view() / get_queryset() / permissions
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     View layer (CBV mixins over Django generics)              │
├────────────────────┬────────────────────┬────────────────────┬───────────────┤
│ CrudView base      │ Concrete views     │ Feature mixins     │ Extensions    │
│ `lib/view/base.py` │ `lib/views/*.py`   │ `lib/views/        │ `crud_views_  │
│ buttons, context,  │ List/Detail/Create │  mixins.py`        │  guardian/`   │
│ action_menu,       │ Update/Delete/     │ `lib/crispy/`      │ `crud_views_  │
│ visibility         │ Action/Card/Form   │ `lib/formsets/`    │  workflow/`   │
│                    │                    │ `lib/conditional/` │ `..._poly..`  │
│                    │                    │ `lib/breadcrumb.py`│ `..._object_  │
│                    │                    │ `lib/resource.py`  │  detail/`     │
└────────┬───────────┴─────────┬──────────┴─────────┬──────────┴───────┬───────┘
         │                     │                    │                  │
         ▼                     ▼                    ▼                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     Presentation layer                                        │
│  Template tags `src/crud_views/templatetags/crud_views.py` (+ _formsets.py)   │
│  Templates     `src/crud_views/templates/crud_views/` (Bootstrap 5 only)      │
│  JS/CSS        `src/crud_views/static/crud_views/{js,css}/`                   │
│  Icons / button classes `lib/icons.py`, `lib/button_classes.py`               │
│  Assets registry `lib/assets.py`, django-pipeline bridge `lib/pipeline.py`    │
└──────────────────────────────────────────────────────────────────────────────┘
         ▲
         │ validated at startup
┌──────────────────────────────────────────────────────────────────────────────┐
│  Cross-cutting: settings `lib/settings.py` · system checks `checks.py` +      │
│  `lib/check.py` · exceptions `lib/exceptions.py` · session `lib/session.py`   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `ViewSet` | Pydantic registry of one model's views; global name registry; PK auto-detection; URL pattern generation; parent-aware queryset; permission map | `src/crud_views/lib/viewset/__init__.py` |
| `ParentViewSet` | Declares nesting (parent name, FK attribute, URL kwarg `<parent>_pk`, m2m-through) | `src/crud_views/lib/viewset/parentviewset.py` |
| `PrimaryKeys` | Regex fragments for UUID/INT/STR PKs, `get_path_pk()` | `src/crud_views/lib/viewset/path_regs.py` |
| `CrudViewMetaClass` | On class creation: registers any class with `cv_viewset` under its `cv_key`, defaults `model` from ViewSet | `src/crud_views/lib/view/meta.py` |
| `CrudView` | Mixin base: sibling URL building, action context/button data, label/header rendering, origin (cancel/success) keys, modal support, transaction boundary, class-level checks | `src/crud_views/lib/view/base.py` |
| `CrudViewPermissionRequiredMixin` | Maps `cv_permission` short key (`view`/`add`/`change`/`delete`) to Django perm via ViewSet; secondary `cv_action_enabled` gate | `src/crud_views/lib/view/base.py` |
| `ContextButton` family | Toolbar button definitions (`ContextButton`, `ParentContextButton`, `ChildContextButton`, `SiblingContextButton`, `FilterContextButton`) | `src/crud_views/lib/view/buttons.py` |
| `ViewContext` | Pydantic carrier `{view, object}` passed to label/button rendering | `src/crud_views/lib/view/context.py` |
| Action menu / visibility | Split actions inline vs overflow menu (`ActionGroup`), hide/disable resolution (`cv_resolve_action`) | `src/crud_views/lib/view/action_menu.py`, `src/crud_views/lib/view/visibility.py` |
| Concrete views | `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`, `ActionView`, `OrderedUp/DownView`, `CardListView`, `CustomFormView`, `RedirectChildView`, `ManageView` | `src/crud_views/lib/views/` |
| `CrudViewProcessFormMixin` | Replaces Django's `ProcessFormView.post` with hookable write pipeline in `transaction.atomic()` | `src/crud_views/lib/views/mixins.py` |
| Table/filter mixins | `ListViewTableMixin` (django-tables2), `ListViewTableFilterMixin` (django-filter + session persistence), `CardOrderMixin` | `src/crud_views/lib/views/mixins.py` |
| Crispy integration | `CrispyModelForm`, `CrispyForm`, `CrispyDeleteForm`, `CrispyViewMixin`, `Column1..12` | `src/crud_views/lib/crispy/` |
| Formsets | Nested inline formsets (`FormSet`, `FormSets`, `FormSetMixin`, render tree `XFormSet`) | `src/crud_views/lib/formsets/` |
| Conditional | Toggle-driven field groups / formsets (`ConditionalGroup`, `ConditionalFormSet`, `ToggleGroup`) | `src/crud_views/lib/conditional/` |
| `Resource` | Non-ORM rows (Pydantic) via `cv_get_items`/`cv_get_item`; `ResourceViewMixin` swaps ORM entry points | `src/crud_views/lib/resource.py` |
| Breadcrumb | `CrudViewBreadcrumbMixin` builds ancestor trail from ViewSet parents | `src/crud_views/lib/breadcrumb.py` |
| Settings | `CrudViewsSettings` singleton reading `CRUD_VIEWS_*` | `src/crud_views/lib/settings.py` |
| Checks | `Check*` Pydantic check objects (`viewset.E###`) + Django check registration (`crud_views.E###`) | `src/crud_views/lib/check.py`, `src/crud_views/checks.py` |
| Template tags | `{% cv_context_actions %}`, `{% cv_list_action %}`, `{% cv_header %}`, `{% cv_js %}`, `{% cv_config %}`, ... | `src/crud_views/templatetags/crud_views.py` |
| Assets | Registry of JS/CSS bundles emitted by `{% cv_js %}`/`{% cv_css %}`; SRI support; pipeline bridge | `src/crud_views/lib/assets.py`, `src/crud_views/lib/pipeline.py`, `src/crud_views/lib/vendor.py` |
| Icons / button classes | Semantic icon registry (`prefix:name`) and CSS class registry per location/slot | `src/crud_views/lib/icons.py`, `src/crud_views/lib/button_classes.py` |
| Guardian ext. | `GuardianViewSet`, per-object permission mixins and views | `src/crud_views_guardian/lib/` |
| Workflow ext. | `WorkflowView` (django-fsm transitions as form), `WorkflowModelMixin`, `WorkflowInfo` audit model | `src/crud_views_workflow/lib/`, `src/crud_views_workflow/models.py` |
| Polymorphic ext. | Content-type select → type-specific create/update/detail/delete | `src/crud_views_polymorphic/lib/` |
| Object detail ext. | `ObjectDetailView` property grid with layout packs and type templates | `src/crud_views_object_detail/lib/` |

## Pattern Overview

**Overall:** Registry + metaclass-driven Class-Based-View composition (a "ViewSet" router over Django generic CBVs), packaged as a reusable multi-app Django library.

**Key Characteristics:**

- Declarative configuration: behavior is driven by `cv_*` class attributes; methods are overridable hooks (`cv_form_valid`, `cv_on_commit`, `cv_has_access`, `cv_action_enabled`).
- Registration at import time: defining a view class with `cv_viewset = vs` registers it (`CrudViewMetaClass.__new__` → `ViewSet.register_view_class`). Instantiating a `ViewSet` registers it in the module-global `_REGISTRY` by `name`.
- Views know siblings by key, never by class: `self.cv_get_url(key="detail", obj=obj)`, `self.cv_viewset.get_view_class("list")`.
- Three-level configuration fallback: view attribute → ViewSet field → `crud_views_settings` (see `CrudView.cv_first_inline_keys`, `cv_get_inaccessible_actions`, `cv_get_extends_template` in `src/crud_views/lib/view/base.py`).
- Pydantic everywhere for config objects: `ViewSet`, `ParentViewSet`, `ContextButton`, `CardAction`, `ViewContext`, `Check`, `FormSet`, `Resource`, `CrudViewsSettings`.
- Fail-at-startup validation: every ViewSet/view yields `Check` objects consumed by Django's system check framework.
- Extensions are separate Django apps that subclass core classes (`GuardianViewSet(ViewSet)`, `WorkflowView(CustomFormView)`) — core never imports extensions.

## Layers

**Registry / Routing:**

- Purpose: Hold the views of one model, compute URL regexes, resolve sibling/parent/child views.
- Location: `src/crud_views/lib/viewset/`
- Contains: `ViewSet`, `ParentViewSet`, `PrimaryKeys`, `_REGISTRY` + `_REGISTRY_LOCK`.
- Depends on: `crud_views.lib.view` (CrudView, ContextButton), `crud_views.lib.views.manage.ManageView`, `crud_views.lib.settings`, `crud_views.lib.resource`.
- Used by: consumer `urls.py` (`urlpatterns += vs.urlpatterns`), every `CrudView` via `cv_viewset`, `checks.py`.

**View base:**

- Purpose: ViewSet-aware behavior shared by all views (not a Django view itself).
- Location: `src/crud_views/lib/view/`
- Contains: `CrudView`, `CrudViewPermissionRequiredMixin`, buttons, card actions, label mode / variant enums, action menu splitting, visibility resolution.
- Depends on: `crud_views.lib.check`, `crud_views.lib.settings`, `crud_views.lib.exceptions`, Django auth/urls/templates.
- Used by: `src/crud_views/lib/views/*`, extension packages, template tags.

**Concrete views:**

- Purpose: Combine `CrudView` with a Django generic CBV and defaults (template, `cv_key`, `cv_path`, label snippets, icons).
- Location: `src/crud_views/lib/views/`
- Contains: one module per view type, plus `mixins.py`.
- Depends on: `crud_views.lib.view`, Django generics, django-tables2, django-filter, crispy-forms.
- Used by: consumer code; extensions (`crud_views_polymorphic/lib/create.py` subclasses `CreateView`, etc.).

**Feature modules:**

- Purpose: Optional capabilities composed in as mixins.
- Location: `src/crud_views/lib/crispy/`, `src/crud_views/lib/formsets/`, `src/crud_views/lib/conditional/`, `src/crud_views/lib/table/`, `src/crud_views/lib/breadcrumb.py`, `src/crud_views/lib/resource.py`.
- Depends on: view base, third-party UI libs.
- Used by: consumer views via MRO (mixins listed before the base view).

**Presentation:**

- Purpose: Render headers, buttons, menus, forms, tables; ship JS behavior.
- Location: `src/crud_views/templatetags/`, `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/`.
- Depends on: `view` in the template context being a `CrudView` (asserted in `cv_get_view()` in `src/crud_views/templatetags/crud_views.py`).
- Used by: consumer base template (must provide `{% block cv_content %}` and load `{% cv_config %}`, `{% cv_js %}`, `{% cv_css %}`).

**Cross-cutting:**

- Purpose: Settings, validation, errors, session persistence.
- Location: `src/crud_views/lib/settings.py`, `src/crud_views/lib/check.py`, `src/crud_views/checks.py`, `src/crud_views/lib/exceptions.py`, `src/crud_views/lib/session.py`, `src/crud_views/lib/context_processor.py`.

## Data Flow

### Startup / Registration Path

1. Consumer module instantiates `cv_author = ViewSet(model=Author, name="author")`; `ViewSet.register` model validator auto-detects `pk` regex, adds to `_REGISTRY`, and creates an `AutoManageView` via `type(...)` (`src/crud_views/lib/viewset/__init__.py:113-146`).
2. Each `class AuthorListView(..., ListViewPermissionRequired): cv_viewset = cv_author` triggers `CrudViewMetaClass.__new__` → `cv_viewset.register_view_class(cv_key, cls)` and sets `model` (`src/crud_views/lib/view/meta.py:15-29`, `src/crud_views/lib/viewset/__init__.py:306-314`).
3. `urls.py` reads `cv_author.urlpatterns` (cached) → one `re_path` per key: `^[parent_prefix/parent_pk/]prefix/[pk/]path/[contribute]$`, name `[app:]<viewset>-<key>` (`src/crud_views/lib/viewset/__init__.py:391-422`).
4. `CrudViewsConfig.ready()` imports `crud_views.checks` (`src/crud_views/apps.py:8-9`); `check_viewsets` iterates `ViewSet.checks_all()` → `view.checks()` → `Check.messages()` (`src/crud_views/checks.py:19-28`).

### Primary Request Path (form views: create/update/custom form/workflow)

1. Django resolves URL → `view_class.as_view()`; `CrudView.dispatch` wraps super and patches `Vary: X-CV-Modal` (`src/crud_views/lib/view/base.py:214-218`).
2. Permission phase: `CrudViewPermissionRequiredMixin.permission_required` resolves `cv_permission` via `cv_viewset.permissions`; `has_permission` additionally calls `cv_action_enabled(user, cv_get_action_object())` (`src/crud_views/lib/view/base.py:852-873`).
3. GET: Django generic view renders `template_name` (e.g. `crud_views/view_create.html`), which `{% extends cv_extends %}` and includes `view.cv_content_template`; modal requests get `crud_views/modal/content.html` (`src/crud_views/lib/view/base.py:209-212`).
4. POST: `CrudViewProcessFormMixin.post` → `get_context_data` → `cv_post_hook` → `cv_form_is_valid` (`src/crud_views/lib/views/mixins.py:30-46`).
5. Valid: `cv_form_valid_process` runs `cv_form_valid` + `cv_form_valid_hook` inside `cv_get_atomic()`; schedules `cv_on_commit` via `transaction.on_commit` (`src/crud_views/lib/views/mixins.py:48-57`).
6. Redirect: `cv_form_valid_redirect` → `get_success_url()` → `cv_get_url(cv_get_success_key(obj))`; modal requests receive `204` + `X-CV-Redirect` (`src/crud_views/lib/views/mixins.py:101-112`, `src/crud_views/lib/view/base.py:196-199`).
7. Invalid: `cv_form_invalid` re-renders; modal requests get status `422` (`src/crud_views/lib/views/mixins.py:85-93`).

### Action (POST-only) Path

1. `ActionView.post` loads `self.object`, builds context, calls `cv_action_process` (`src/crud_views/lib/views/action.py:16-21`).
2. `cv_action_process` runs `action(context) -> bool` inside `cv_get_atomic()`; success → message + `cv_on_commit`; failure → error message (`src/crud_views/lib/views/action.py:23-36`).
3. Redirects to `get_success_url()`.

### Button / Action Rendering Path

1. Template calls `{% cv_context_actions %}` or `{% cv_list_action key object %}` (`src/crud_views/templatetags/crud_views.py:117-120`, `:299-303`).
2. Tag → `view.cv_get_context(key, obj, user, request, location=...)` (`src/crud_views/lib/view/base.py:612-634`).
3. `_cv_get_action_context` checks for a `ContextButton` with that key (view-level first, then ViewSet-level); otherwise resolves sibling class, computes `cv_url` (with `?cv_from=` origin), `cv_access` (`cls.cv_has_access`), `cv_action_enabled`, then `cls.cv_get_dict()` (`src/crud_views/lib/view/base.py:636-681`).
4. `cv_resolve_action` returns `None` (hide), a disabled copy, or an enabled copy (`src/crud_views/lib/view/visibility.py:1-20`).
5. `cv_split_actions` divides inline buttons vs overflow menu when `*_actions_inline` is configured (`src/crud_views/lib/view/action_menu.py:88`).
6. Leaf templates in `src/crud_views/templates/crud_views/tags/` render buttons; classes come from `lib/button_classes.py`, icons from `lib/icons.py`.

### Nested (Parent/Child) Flow

1. Child ViewSet declares `parent=ParentViewSet(name="publisher")`; URL gains `publisher/(?P<publisher_pk>...)/` prefix (`src/crud_views/lib/viewset/__init__.py:350-365`).
2. `ViewSet.get_queryset(view)` filters `parent_attr__pk=view.kwargs["publisher_pk"]` across the parent chain (`src/crud_views/lib/viewset/__init__.py:269-304`).
3. `CreateViewParentMixin.cv_form_valid` sets the FK (or m2m `add`) from `cv_get_parent_object()` (`src/crud_views/lib/views/create.py:44-73`).
4. `cv_get_router_and_args` copies parent kwargs from `self.kwargs` into every sibling URL (`src/crud_views/lib/view/base.py:481-514`).

### Filter Persistence Flow

1. `ListViewTableFilterMixin.get` stores/restores the query string in the session via `SessionData.from_view(self)` (`src/crud_views/lib/views/mixins.py:357-399`).
2. `ListViewTableFilterMixin.post` receives JSON `{filter_expanded}` from `list.filter.js` and persists it (`src/crud_views/lib/views/mixins.py:336-355`).

**State Management:**

- Process-global, import-time state: `_REGISTRY` (ViewSets), each ViewSet's `_views`, `ViewSet._default_permissions` cache, asset `_REGISTRY` (`src/crud_views/lib/assets.py`), icon/button-class caches reset on `setting_changed` (`src/crud_views/lib/icons.py`, `src/crud_views/lib/button_classes.py`).
- Per-user state: Django session under `CRUD_VIEWS_SESSION_DATA_KEY` (default `"viewset"`), hierarchical app → viewset-key → data (`src/crud_views/lib/session.py`).
- Per-request state: view instance attributes (`self.object`, `self.kwargs`) and the `context` dict passed through hooks.
- Client config: `{% cv_config %}` writes `#cv-config` data attributes (CSRF token, path) read by `cvGetConfig()` in `src/crud_views/static/crud_views/js/viewset.js`.

## Key Abstractions

**ViewSet:**

- Purpose: The unit of a CRUD resource; router + registry + permission source.
- Examples: `src/crud_views/lib/viewset/__init__.py`, `src/crud_views_guardian/lib/viewset.py` (`GuardianViewSet`)
- Pattern: Pydantic `BaseModel` with `model_validator(mode="after")` side effects and `PrivateAttr` storage.

**CrudView:**

- Purpose: ViewSet-aware mixin; always combined with a Django generic view.
- Examples: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/list.py`, `src/crud_views/lib/views/create.py`
- Pattern: Metaclass registration; `cv_`-prefixed attributes; classmethods for anything needed without an instance (`cv_has_access`, `cv_get_dict`, `checks`).

**`*PermissionRequired` variant:**

- Purpose: Same view plus Django permission enforcement.
- Examples: `CreateViewPermissionRequired(CrudViewPermissionRequiredMixin, CreateView)` in `src/crud_views/lib/views/create.py:40`
- Pattern: Every concrete view `XView` has `XViewPermissionRequired` setting `cv_permission`.

**ContextButton:**

- Purpose: A toolbar button keyed by name that may target a sibling, parent, child, or other ViewSet.
- Examples: `src/crud_views/lib/view/buttons.py`
- Pattern: Pydantic model with `get_context(ViewContext) -> dict` and `cv_check_target(viewset)` for E255.

**Check:**

- Purpose: Declarative startup validation.
- Examples: `CheckAttributeReg`, `CheckTemplateOrCode`, `CheckExpression`, `CheckUnknownAttributes` in `src/crud_views/lib/check.py`
- Pattern: `cls.checks()` generator yields `Check` instances; subclasses chain with `yield from super().checks()`.

**Resource:**

- Purpose: Table-shaped non-ORM data (S3, APIs) rendered through a ViewSet (read-only views).
- Examples: `src/crud_views/lib/resource.py`, `tests/test1/app/resources.py`, `examples/bootstrap5/resources/`
- Pattern: Pydantic rows with Django-like `_meta` (`ResourceOptions`); `ResourceViewMixin` must be FIRST base.

**FormSets:**

- Purpose: Nested inline formsets on create/update views.
- Examples: `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/mixins.py`, `tests/test1/app/views_formset.py`
- Pattern: Pydantic tree of `FormSet` definitions cloned per request (`FormSets.clone(cv_view)`), extending `cv_form_is_valid` / `cv_form_valid`.

**Hook methods (template method pattern):**

- `cv_post_hook`, `cv_form_is_valid`, `cv_form_valid`, `cv_form_valid_hook`, `cv_form_invalid_hook`, `cv_on_commit` (`src/crud_views/lib/views/mixins.py`); `action`, `cv_action_success_hook`, `cv_action_error_hook` (`src/crud_views/lib/views/action.py`); `on_transition` (`src/crud_views_workflow/lib/views.py`).

## Entry Points

**Django app configs:**

- Location: `src/crud_views/apps.py` (`CrudViewsConfig`, label `crud_views`), `src/crud_views_workflow/apps.py` (label `cvw`), `src/crud_views_guardian/apps.py` (label `cvg`), `src/crud_views_polymorphic/apps.py` (label `cvp`), `src/crud_views_object_detail/apps.py` (label `cvod`)
- Triggers: `INSTALLED_APPS` loading.
- Responsibilities: `ready()` imports `crud_views.checks` / `crud_views_workflow.checks` to register system checks.

**ViewSet.urlpatterns:**

- Location: `src/crud_views/lib/viewset/__init__.py:391`
- Triggers: Consumer `urls.py`.
- Responsibilities: Produce `re_path` resolvers for every registered view.

**Template tag library `crud_views`:**

- Location: `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templatetags/crud_views_formsets.py`, `src/crud_views_object_detail/templatetags/crud_views_object_detail.py`
- Triggers: `{% load crud_views %}` in templates.

**Context processor:**

- Location: `src/crud_views/lib/context_processor.py` (`crud_views_context`)
- Responsibilities: Expose `crud_views_settings.as_dict` (`viewset.extends`, JS/CSS paths).

**Management commands:**

- Location: `src/crud_views/management/commands/cv_assets.py` (list asset registry / delivery), `src/crud_views/management/commands/crud_views_show.py` (placeholder, no-op).

**Public API surface:**

- `crud_views.lib.viewset` (`ViewSet`, `ParentViewSet`), `crud_views.lib.views` (`__all__` in `src/crud_views/lib/views/__init__.py`), `crud_views.lib.view`, `crud_views.lib.crispy`, `crud_views.lib.table`, `crud_views.lib.formsets`, `crud_views.lib.conditional`, `crud_views_polymorphic.lib`, `crud_views_workflow.lib` (lazy), `crud_views_object_detail.lib` (lazy). Guarded by `tests/test1/test_public_api_surface.py`.

## Architectural Constraints

- **Threading:** Standard Django sync request model. Registry mutation is guarded by `_REGISTRY_LOCK` (`threading.Lock`) in `src/crud_views/lib/viewset/__init__.py` and `_LOCK` in `src/crud_views/lib/assets.py`; registration is expected to finish at import time before serving.
- **Global state:** `_REGISTRY` (`src/crud_views/lib/viewset/__init__.py:41`), `crud_views_settings` singleton (`src/crud_views/lib/settings.py:279`, evaluated at import — class attribute defaults like `cv_context_actions = crud_views_settings.create_context_actions` are bound at import), asset `_REGISTRY` (`src/crud_views/lib/assets.py`), icon/button-class caches (`src/crud_views/lib/icons.py`, `src/crud_views/lib/button_classes.py`), `ViewSet.urlpatterns` `cached_property`.
- **ViewSet names are global and unique:** a duplicate `name` raises `ViewSetError` at instantiation (`src/crud_views/lib/viewset/__init__.py:134-139`). Tests must use distinct names per ViewSet.
- **Circular imports:** `crud_views.lib.viewset` ↔ `crud_views.lib.resource` / `crud_views.lib.view.context`. `src/crud_views/lib/resource.py` must remain a leaf (no `crud_views.lib.viewset` imports, documented at its top); `ViewContext.object` is typed `Any` for the same reason (`src/crud_views/lib/view/context.py`). `settings.py` defers view imports into methods. `ParentViewSet.viewset` imports `ViewSet` lazily.
- **Import safety before `django.setup()`:** `crud_views_workflow.lib` and `crud_views_object_detail.lib` use PEP 562 lazy `__getattr__` so model modules can import mixins early (`src/crud_views_workflow/lib/__init__.py`). Verified by `tests/test1/test_import_safety.py`.
- **MRO ordering:** Mixins go before the base view (`CrispyViewMixin, MessageMixin, CreateViewPermissionRequired`); `ResourceViewMixin` and `ObjectDetailMixin` must be first; `CrudViewPermissionRequiredMixin` precedes the concrete view in `*PermissionRequired` classes.
- **Theme:** Bootstrap 5 only; `theme_path` is hard-coded to `"crud_views"` (`src/crud_views/lib/settings.py:228`). JS touches UI libraries only through `cv.adapters` (`src/crud_views/static/crud_views/js/adapters.js`); no jQuery (guarded by `tests/test1/test_js_no_jquery_guard.py`).
- **Resource ViewSets:** read-only (E262), leaf-only in nesting (E261), explicit `resource_permissions` (E260); no ManageView.
- **Strict mode:** `CRUD_VIEWS_STRICT` (default `DEBUG`) makes `ignore_exception` re-raise (`src/crud_views/lib/exceptions.py:32-60`).

## Anti-Patterns

### Hard-coding sibling URLs or view classes

**What happens:** Calling `reverse("author-detail", ...)` or importing a sibling view class directly inside a view/template.
**Why it's wrong:** Loses parent kwargs, `app` namespace, the `list`→`card` fallback, and origin (`cv_from`) handling.
**Do this instead:** Use `self.cv_get_url(key="detail", obj=obj)` / `self.cv_get_child_url(name, key, obj)` (`src/crud_views/lib/view/base.py:516`, `:776`) or `{% cv_context_url "detail" object as url %}`.

### Side effects inside the write phase

**What happens:** Sending mail or enqueuing Celery tasks in `cv_form_valid_hook`, `action()` or `on_transition`.
**Why it's wrong:** These run inside `transaction.atomic()`; a later rollback leaves the side effect done.
**Do this instead:** Override `cv_on_commit(self, context)` (`src/crud_views/lib/view/base.py:235`), scheduled via `transaction.on_commit` in `src/crud_views/lib/views/mixins.py:57`.

### Overriding `post()` on form views without the write pipeline

**What happens:** Subclass replaces `post()` and saves directly.
**Why it's wrong:** Skips atomic boundary, `cv_on_commit`, modal `204/422` handling, and formset validation hooks.
**Do this instead:** Override `cv_form_valid` / `cv_form_is_valid`, or call `self.cv_form_valid_process(context)` (`src/crud_views/lib/views/mixins.py:48`).

### Mutating shared default lists

**What happens:** `cv_context_actions.append("x")` on a view class.
**Why it's wrong:** Defaults are the list objects from `crud_views_settings` shared across classes.
**Do this instead:** Assign a new list (`cv_context_actions = [*base, "x"]`) — copy-on-write as in `ViewSet.register_view_class` (`src/crud_views/lib/viewset/__init__.py:311-314`).

### Importing `crud_views.lib.viewset` from `resource.py` or eager imports in lazy `lib/__init__.py`

**What happens:** Adding a convenience import into a leaf module.
**Why it's wrong:** Reintroduces partially-initialized-module `ImportError` when a consumer's `models.py` is imported first.
**Do this instead:** Keep `src/crud_views/lib/resource.py` a leaf; add new extension exports to the `_EXPORTS` map in `src/crud_views_workflow/lib/__init__.py` / `src/crud_views_object_detail/lib/__init__.py`.

## Error Handling

**Strategy:** Fail loudly at configuration time (system checks + `cv_raise`), degrade gracefully at render time (skip unresolvable buttons), raise in strict mode.

**Patterns:**

- Configuration assertions: `cv_raise(expression, msg, exception=ViewSetError)` (`src/crud_views/lib/exceptions.py:27`); exception types `ViewSetNotFoundError`, `ViewSetKeyFoundError`, `ViewSetError`, `CrudViewError`, `ParentViewSetError`.
- Startup validation: `Check` subclasses produce `django.core.checks.Error`/`Warning` with ids `viewset.E###` / `viewset.W###` (`src/crud_views/lib/check.py:37`), plus `crud_views.E###` package-level checks (`src/crud_views/checks.py`, `src/crud_views/lib/settings.py` `check_messages`).
- Render-time tolerance: unregistered keys return `{}` from `_cv_get_action_context` and are skipped (`src/crud_views/lib/view/base.py:644-656`); `ignore_exception` decorator logs and returns default unless strict.
- HTTP errors: `get_object_or_404` for parents, `Http404` from `Resource.cv_get_item`, `PermissionDenied` from guardian mixins, `BadRequest` for malformed filter JSON, `SuspiciousOperation` for invalid workflow transitions.

## Cross-Cutting Concerns

**Logging:** Python `logging` via module loggers (`logging.getLogger(__name__)` in `src/crud_views/lib/exceptions.py`, `src/crud_views/lib/views/delete.py`); used mainly for swallowed exceptions.
**Validation:** Pydantic validators on config models; Django system checks for views/ViewSets/settings/icons/button classes/assets/pipeline; django forms for user input.
**Authentication / Authorization:** Django auth `PermissionRequiredMixin` via `CrudViewPermissionRequiredMixin`; permission map from `ContentType`/`Permission` rows (`ViewSet.default_permissions`); state gate `cv_action_enabled`; per-object via `crud_views_guardian` mixins (`src/crud_views_guardian/lib/mixins.py`).
**Transactions:** `cv_atomic` / `cv_get_atomic()` / `cv_get_db_alias()` honoring `DATABASE_ROUTERS` (`src/crud_views/lib/view/base.py:220-240`).
**i18n:** `gettext_lazy` in Python, `locale/de` per package; `settings_i18n.py` at repo root for message extraction.
**CSP / SRI:** nonce resolved from `CRUD_VIEWS_CSP_NONCE_ATTR` in `cv_js`/`cv_css`; `Asset(integrity=...)` for external URLs (`src/crud_views/lib/assets.py`).

---

*Architecture analysis: 2026-10-25*
