# API stability

From release **1.0.0** on, django-crud-views follows [semantic versioning](https://semver.org/):
breaking changes to the **public API** defined on this page only happen in major releases.
This policy is effective as of 0.14.0 so that 1.0.0 can ship against a settled surface.

## The rule

The public API is the set of names listed below — the same names shown in the
[reference documentation](../reference/index.md). Everything else is internal:

- any module or name not listed here,
- all names prefixed with an underscore (`_`),
- template internals (block structure and context variables not documented in the reference),
- anything imported *by* django-crud-views from its dependencies.

Internal APIs may change in any release without notice.

## Public API

### `crud_views` (core)

**ViewSets** — `crud_views.lib.viewset`:
`ViewSet`, `ParentViewSet`

**View base** — `crud_views.lib.view`:
`CrudView`, `CrudViewPermissionRequiredMixin`

**Views** — `crud_views.lib.views`:
`ListView`, `DetailView`, `DetailCustomView`, `CreateView`, `UpdateView`, `DeleteView`,
`ActionView`, `OrderedUpView`, `OrderedDownView`, `CustomFormView`, `CustomFormNoObjectView`,
`CardListView`, `ManageView` — each with its `*PermissionRequired` variant — plus the mixins
`CreateViewParentMixin`, `ListViewTableMixin`, `ListViewTableFilterMixin`, `MessageMixin`

**Crispy forms integration** — `crud_views.lib.crispy`:
`CrispyViewMixin`, `CrispyModelForm`, `CrispyForm`, `CrispyDeleteForm`,
`Column1` … `Column12`

**Formsets (declaration surface)** — `crud_views.lib.formsets`:
`FormSetMixin`, `FormSets`, `FormSet`, `InlineFormSet`, `Formsets`, `FormControl` — i.e.
exactly the names exported by the package. The formsets machinery behind them (rendering
tree, per-formset plumbing) is internal, and stays internal in 1.0.

**Resources** — `crud_views.lib.resource`:
`Resource`, `ResourceViewMixin`

**Settings**: all `CRUD_VIEWS_*` settings documented in the
[settings reference](../reference/settings.md).

**Template tags**: the tags documented in the reference for the `crud_views` and
`crud_views_formsets` tag libraries.

**Declared attributes and hooks**: the documented `cv_*` class attributes of the classes
above, and the documented overridable hooks — e.g. `cv_form_valid` (framework work step),
`cv_form_valid_hook` (user extension point), `cv_post_hook`, `cv_form_invalid_hook`,
`cv_form_valid_redirect`.

### `crud_views_workflow`

Public import path: `crud_views_workflow.lib` —
`WorkflowView`, `WorkflowViewPermissionRequired`, `WorkflowModelMixin`, `WorkflowForm`,
`BadgeEnum`, `WorkflowComment`. The `WorkflowInfo` model stays at `crud_views_workflow.models`,
and the `on_transition` hook is the documented overridable method on `WorkflowView`.

### `crud_views_polymorphic`

Public import path: `crud_views_polymorphic.lib` —
`PolymorphicCreateSelectView`, `PolymorphicCreateView`, `PolymorphicUpdateView`,
`PolymorphicDeleteView`, `PolymorphicDetailView` — each with its `*PermissionRequired`
variant — plus the `PolymorphicContentTypeForm` used by the create-select flow.

### `crud_views_guardian`

`GuardianViewSet`, `GuardianManageView`, and the `Guardian*PermissionRequired` view variants
(list, card list, detail, detail custom, create, update, delete, action).

## Deprecation policy (post-1.0)

- Public-API breaking changes happen only in **major** releases.
- A name slated for removal is deprecated first: it keeps working and emits a
  `DeprecationWarning` for the remainder of the current major cycle, and is removed no
  earlier than the next major release.
- Every deprecation and removal is recorded in the CHANGELOG with a migration hint.
