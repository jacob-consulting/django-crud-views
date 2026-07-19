# Reference

## Views

- [ListView](list_view.md) — display a list of model instances with tables and filters
- [CardListView](card-list-view.md) — display model instances as cards instead of table rows
- [DetailView](detail_view.md) — display a single model instance with a custom template
- [ObjectDetailView](object_detail_view.md) — display a single model instance with structured, auto-detected property groups (optional `crud_views_object_detail` app)
- [CreateView](create_view.md) — create new model instances with forms
- [UpdateView](update_view.md) — update existing model instances with forms
- [DeleteView](delete_view.md) — delete model instances with confirmation
- [CustomFormView](custom_form_view.md) — a custom form attached to (or independent of) an existing object
- [ActionView](action_view.md) — run a side-effecting action on an object with success/error messages
- [OrderedView](ordered_view.md) — up/down reordering for django-ordered-model instances
- [WorkflowView](workflow_view.md) — execute FSM state-machine transitions with audit history
- [PolymorphicView](polymorphic_view.md) — CRUD views for django-polymorphic models
- [Resources](resources.md) — list/detail/action views over non-ORM, table-shaped data

## Nesting & Forms

- [Nested ViewSets](nested.md) — parent/child ViewSets with nested URLs and auto-filtered querysets
- [Formsets](formsets.md) — inline editing of related child objects on create/update views
- [Conditional Field-Groups & Formsets](conditional.md) — toggle a group of fields or a first-level formset on/off

## Navigation & UI

- [Context Buttons](context_buttons.md) — context action buttons for navigation within and across viewsets
- [Breadcrumb](breadcrumb.md) — a Bootstrap breadcrumb following the ViewSet hierarchy
- [Modals](modals.md) — open supported views in a Bootstrap modal instead of a full page
- [Conditionally disabling an action](action_enabled.md) — disable an action a user is otherwise permitted to perform, based on object state

## Extensions

- [Per-Object Permissions (django-guardian)](guardian.md) — object-level permission checking via django-guardian

## Theming & Configuration

- [Base template](templates.md) — control which base template CRUD pages extend
- [Custom themes](theme.md) — replace crud_views' own templates with a theme app
- [Asset registry](assets.md) — register JavaScript/CSS bundles and vendor third-party files
- [Settings](settings.md) — all available settings for django-crud-views
