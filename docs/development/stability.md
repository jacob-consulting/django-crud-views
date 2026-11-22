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
`CrudView`, `CrudViewPermissionRequiredMixin`, `Variant` (`crud_views.lib.view.variant`)

**Button classes** — `crud_views.lib.button_classes`:
`register_button_classes`, `get_button_classes`, `get_button_class`

**Views** — `crud_views.lib.views`:
`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`,
`ActionView`, `OrderedUpView`, `OrderedDownView`, `CustomFormView`, `CustomFormNoObjectView`,
`CardListView`, `ManageView` — each with its `*PermissionRequired` variant — plus the mixins
`CreateViewParentMixin`, `ListViewTableMixin`, `ListViewTableFilterMixin`, `MessageMixin`

`DetailView` is the simple, template-driven detail view. Rich property-display detail
(structured property groups, previously on `DetailView` via django-object-detail) lives in the
optional `crud_views_object_detail` app as `ObjectDetailView`
(`from crud_views_object_detail.lib import ObjectDetailView`).

**Crispy forms integration** — `crud_views.lib.crispy`:
`CrispyViewMixin`, `CrispyModelForm`, `CrispyForm`, `CrispyDeleteForm`, `Submit`, `Button`, `Reset`,
`Column1` … `Column12`

**Formsets (declaration surface)** — `crud_views.lib.formsets`:
`FormSetMixin`, `FormSets`, `FormSet`, `InlineFormSet`, `Formsets`, `FormControl` — i.e.
exactly the names exported by the package. The formsets machinery behind them (rendering
tree, per-formset plumbing) is internal, and stays internal in 1.0.

**Resources** — `crud_views.lib.resource`:
`Resource`, `ResourceViewMixin`

**ViewSet Navigation** — `crud_views.lib.navbar`:
`NavBar`, `NavItem`, `CrudViewNavBarMixin`, the per-view `cv_navbar` attachment, and the
`{% cv_navbar %}`, `{% cv_navbar_identity %}` and `{% cv_navbar_items %}` tags in the `crud_views` tag library. The declaration fields and supported behavior in the
[ViewSet Navigation reference](../reference/navbar.md) are stable at 1.0 under this policy.
The override contract includes exactly `crud_views/tags/navbar.html`,
`crud_views/tags/navbar_identity.html`, and `crud_views/tags/navbar_items.html`, with the documented
`cv_navbar` value and fields `object`, `label`, `icon`, `items`, `template`; item fields are `label`, `icon`,
`url`, `active`. See [ViewSet Navigation context](../reference/templates.md#viewset-navigation-context) for their meanings
and independent empty guards. The six ordinary class keys `navbar:wrapper`, `navbar:identity`, `navbar:nav`,
`navbar:item`, `navbar:link` and `navbar:link-active` use the existing registry, theme registration and
project-setting precedence, including empty removal. See their
[defaults](../reference/buttons.md#viewset-navigation-classes) and
[registration recipe](../reference/theme.md#navbar-class-registration).
Supported composition includes the [owner-heading recipe](../reference/navbar.md#owner-as-page-heading)
through existing context and components, retaining view titles, actions, extension blocks and fallback.
Heading hierarchy belongs to the theme; the stock plain identity is unchanged. `NavBar(template=...)`
selects only the full wrapper; component tags and direct includes retain normal independent leaf selection.
Private builders, resolvers, normalization helpers and check carriers remain internal.
There is no navbar-specific provisional exception: public breaking changes follow the major-release,
deprecation and migration policy below.

**Bulk actions** — `crud_views.lib.bulk`:
`BulkSelectionMixin`, `BulkFormViewPermissionRequired` and `BulkConfirmForm`; the attributes
`cv_bulk_actions`, `cv_bulk_max`, `cv_bulk_confirm` and `cv_bulk_objects`; the hooks
`cv_bulk_has_permission(obj)` and `cv_bulk_check(obj)`; and the read-only property `cv_bulk_header`.
The POST fields are `cv_bulk_ids`, `cv_bulk_blocked_ids` and `cv_bulk_stage`; the `cv_bulk_` prefix is reserved.
The override contract includes `crud_views/view_bulk_form.html`, `crud_views/view_bulk_form.content.html`,
`crud_views/snippets/bulk_toolbar.html`, `crud_views/columns/bulk_select.html`,
`crud_views/snippets/message/bulk.html`, `crud_views/snippets/bulk/blocked.html`,
`crud_views/snippets/bulk/eligible.html` and `crud_views/tags/button/bulk.html`. The two review snippets receive
`bulk_review` with `objects` and `blocked`; each blocked item has `pk`, `label` and `reasons`.
The six data attributes are `data-cv-bulk`, `data-cv-bulk-item`, `data-cv-bulk-all`, `data-cv-bulk-count`,
`data-cv-bulk-action` and `data-cv-bulk-enhanced`. The seven class keys are `bulk:toolbar`, `bulk:controls`,
`bulk:select-all`, `bulk:checkbox`, `bulk:actions`, `bulk:card-cell` and `bulk:card-select`, with the
label-mode location `bulk` (floor `both`). Four additional variant keys, `bulk:primary`, `bulk:secondary`,
`bulk:tertiary` and `bulk:danger`, support effective-mode suffixes `:label`, `:icon` and `:both` with normal
presence-based precedence; the seven utility keys do not. The bulk leaf's flat contract is documented in
[Bulk button leaf](../reference/buttons.md#bulk-button-leaf); its data builder remains internal.
These names and the behavior in the
[bulk actions reference](../reference/bulk_actions.md) are stable at 1.0.
There is no bulk-specific provisional exception: public breaking changes follow the major-release,
deprecation and migration policy below.

**Settings**: all `CRUD_VIEWS_*` settings documented in the
[settings reference](../reference/settings.md).

**Template tags**: the tags documented in the reference for the `crud_views` and
`crud_views_formsets` tag libraries.

**Declared attributes and hooks**: the documented `cv_*` class attributes of the classes
above, and the documented overridable hooks — e.g. `cv_form_valid` (framework work step),
`cv_form_valid_hook` (user extension point), `cv_post_hook`, `cv_form_invalid_hook`,
`cv_form_valid_redirect`, and the transaction API: `cv_atomic`, `cv_get_atomic`,
`cv_get_db_alias`, `cv_on_commit`, `cv_form_valid_process`, `cv_action_process`
(see [Request lifecycle, transactions & hooks](../reference/request_lifecycle.md)).
A bulk destination (`BulkFormViewPermissionRequired`) does not call `cv_form_valid_process`, because it runs
`cv_form_valid` and `cv_form_valid_hook` itself inside `cv_get_atomic()` after its eligibility check.
An override of `cv_form_valid_process` has no effect on a bulk destination; applications override
`cv_form_valid` or `cv_form_valid_hook` there, as described in
[How a submission is handled](../reference/bulk_actions.md#how-a-submission-is-handled).

### `crud_views_workflow`

Public import path: `crud_views_workflow.lib` —
`WorkflowView`, `WorkflowViewPermissionRequired`, `WorkflowModelMixin`, `WorkflowForm`,
`BadgeEnum`, `WorkflowComment`. The `WorkflowInfo` model stays at `crud_views_workflow.models`,
and the `on_transition` hook is the documented overridable method on `WorkflowView` (it runs inside the transaction; `context["workflow_info"]` is available in `cv_on_commit`).

### `crud_views_polymorphic`

Public import path: `crud_views_polymorphic.lib` —
`PolymorphicCreateSelectView`, `PolymorphicCreateView`, `PolymorphicUpdateView`,
`PolymorphicDeleteView`, `PolymorphicDetailView` — each with its `*PermissionRequired`
variant — plus the `PolymorphicContentTypeForm` used by the create-select flow.

### `crud_views_guardian`

`GuardianViewSet`, `GuardianManageView`, and the `Guardian*PermissionRequired` view variants
(list, card list, detail, create, update, delete, action).

## Deprecation policy (post-1.0)

- Public-API breaking changes happen only in **major** releases.
- A name slated for removal is deprecated first: it keeps working and emits a
  `DeprecationWarning` for the remainder of the current major cycle, and is removed no
  earlier than the next major release.
- Every deprecation and removal is recorded in the CHANGELOG with a migration hint.
