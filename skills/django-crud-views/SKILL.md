---
name: django-crud-views
description: "Build Django CRUD interfaces using the django-crud-views package. Use when creating, reading, updating, or deleting model records with class-based views; when wiring up ViewSets, ListViews, DetailViews, CreateViews, UpdateViews, or DeleteViews; when configuring tables with django-tables2, filters with django-filter, or forms with django-crispy-forms; when implementing nested/child resources with ParentViewSet; when adding permission-required views; when integrating django-fsm state machine transitions with WorkflowView or WorkflowViewPermissionRequired; when adding workflow audit history to models with WorkflowModelMixin; when using formsets with FormSetMixin; when working with polymorphic models; when adding per-object permissions with django-guardian via GuardianViewSet and Guardian*ViewPermissionRequired; or any time the codebase imports from crud_views.lib, crud_views_workflow, crud_views_polymorphic, or crud_views_guardian."
---

# django-crud-views

A library that wires together class-based views, django-tables2, django-filter, and django-crispy-forms into a coherent
CRUD framework. Key concepts: a **ViewSet** groups all views for a model and auto-generates URL patterns; each
**CrudView** subclass registers itself with the ViewSet via the `cv_viewset` attribute.

Full API reference: see [references/api-reference.md](references/api-reference.md)

---

## Quick Start — Simple CRUD

### 1. Define the ViewSet

```python
# views/author.py
from crud_views.lib.viewset import ViewSet
from .models import Author

cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")
```

### 2. Add URL patterns

```python
# urls.py
from app.views.author import cv_author

urlpatterns += cv_author.urlpatterns
```

### 3. List view with table

```python
import django_tables2 as tables
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.table.columns import NaturalDayColumn, NaturalTimeColumn
from crud_views.lib.views import ListViewTableMixin, ListViewPermissionRequired

class AuthorTable(Table):
    id = UUIDLinkDetailColumn()
    first_name = tables.Column()
    last_name = tables.Column()
    created_dt = NaturalDayColumn()

class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete"]  # per-row buttons
```

### 4. Create / Update views

```python
from crispy_forms.layout import Row
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin
from crud_views.lib.views import CreateViewPermissionRequired, UpdateViewPermissionRequired, MessageMixin

class AuthorCreateForm(CrispyModelForm):
    submit_label = "Create"
    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]
    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))

class AuthorUpdateForm(AuthorCreateForm):
    submit_label = "Update"

class AuthorCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    form_class = AuthorCreateForm
    cv_viewset = cv_author
    cv_message = "Created author »{object}«"

class AuthorUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message = "Updated author »{object}«"
```

### 5. Delete view

```python
from crud_views.lib.crispy import CrispyDeleteForm
from crud_views.lib.views import DeleteViewPermissionRequired

class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message = "Deleted author »{object}«"
```

### 6. Detail view

```python
from crud_views.lib.views import DetailViewPermissionRequired

class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author

    property_display = [
        {
            "title": "Attributes",
            "icon": "tag",
            "description": "Core author information",
            "properties": [
                "first_name",
                "last_name",
                {"path": "full_name", "detail": "Computed from first and last name"},
                {"path": "id", "title": "UUID"},
            ],
        },
    ]
```

Each entry in `properties` can be a plain string (field or `@property` name), a dict, or an `x()` helper
from `django_object_detail`. Dict keys: `path` (required), `title`, `detail` (tooltip), `type`, `template`,
`link`, `badge`. Use `__` for FK/M2M traversal: `"author__email"`, `"tags"`.

Configure django-object-detail in settings:

```python
INSTALLED_APPS = [..., "django_object_detail", "crud_views", ...]

# Layout pack: "split-card" (default), "accordion", "tabs-vertical", "card-rows",
#              "striped-rows", "table-inline", "list-group-3col"
OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "split-card"
OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "default"

# Icon library: "fontawesome" or "bootstrap" (default)
OBJECT_DETAIL_ICONS_LIBRARY = "fontawesome"
OBJECT_DETAIL_ICONS_TYPE = "solid"  # or "regular", "light", "thin", "duotone"
```

---

## Nested Resources (Child ViewSet)

Add `parent=ParentViewSet(name="author")` to the child ViewSet. Use `CreateViewParentMixin` on the child's create
view to auto-assign the FK. Add `LinkChildColumn` to the parent table to link through.

```python
# views/book.py
from crud_views.lib.viewset import ViewSet, ParentViewSet
from crud_views.lib.table import Table, UUIDLinkDetailColumn, LinkChildColumn
from crud_views.lib.views import CreateViewParentMixin, CreateViewPermissionRequired

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),  # URL: /author/<author_pk>/book/
)

class BookCreateView(CrispyModelViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    form_class = BookCreateForm
    cv_viewset = cv_book

# In the parent AuthorTable, add:
# books = LinkChildColumn(name="book", verbose_name="Books")
```

URLs for `cv_book` must also be added: `urlpatterns += cv_book.urlpatterns`

---

## Filtering

```python
import django_filters
from crud_views.lib.views import ListViewTableFilterMixin
from crud_views.lib.views.list import ListViewFilterFormHelper
from crispy_forms.layout import Layout, Row

class AuthorFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")
    class Meta:
        model = Author
        fields = ["first_name", "last_name"]

class AuthorFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("first_name"), Column4("last_name")))

class AuthorListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper
    cv_viewset = cv_author
```

---

## Ordered Actions (move up/down)

```python
from crud_views.lib.views import OrderedUpViewPermissionRequired, OrderedUpDownPermissionRequired

class AuthorUpView(MessageMixin, OrderedUpViewPermissionRequired):
    cv_viewset = cv_author
    cv_message = "Moved »{object}« up"

class AuthorDownView(MessageMixin, OrderedUpDownPermissionRequired):
    cv_viewset = cv_author
    cv_message = "Moved »{object}« down"

# Add "up" and "down" to cv_list_actions in the list view
```

---

## Custom Form View

`CustomFormView` attaches a custom form to an existing object — use for contact forms, approval actions, etc.

```python
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.views import MessageMixin
from crud_views.lib.crispy import CrispyModelForm, CrispyModelViewMixin, Column12

class AuthorContactForm(CrispyModelForm):
    submit_label = "Send"
    subject = CharField(label="Subject", required=True)
    body = CharField(label="Body", required=True)
    class Meta:
        model = Author
        fields = ["subject", "body"]
    def get_layout_fields(self):
        return Column12("subject"), Column12("body")

class AuthorContactView(MessageMixin, CrispyModelViewMixin, CustomFormViewPermissionRequired):
    cv_key = "contact"      # unique key — auto-registers URL with the ViewSet
    cv_path = "contact"     # URL path segment
    cv_icon_action = "fa-solid fa-envelope"
    cv_viewset = cv_author
    form_class = AuthorContactForm
    cv_message_template_code = "Successfully contacted author »{object}«"
    cv_context_actions = ["parent", "detail", "update", "delete", "contact"]
    cv_header_template_code = "Contact Author"
    cv_paragraph_template_code = "Send a message to the Author"

    def cv_form_valid(self, context):
        form = context["form"]
        # process form.cleaned_data here
        pass
```

Use `CustomFormNoObjectViewPermissionRequired` for forms not tied to a specific instance.

---

## Custom Action View

Subclass `ActionViewPermissionRequired` and implement `action(context)`. Register with a unique `cv_key` and
`cv_path`. Add that key to `cv_list_actions` on the list view to show a per-row button.

---

## Settings (Django `settings.py`)

```python
CRUD_VIEWS = {
    "EXTENDS": "base.html",                    # required: base template
    "MANAGE_VIEWS_ENABLED": "debug_only",      # "yes" | "no" | "debug_only"
    "SESSION_DATA_KEY": "viewset",
    "FILTER_PERSISTENCE": True,
    "FILTER_ICON": "fa-solid fa-filter",
    "FILTER_RESET_BUTTON_CSS_CLASS": "btn btn-secondary",
    "LIST_ACTIONS": ["detail", "update", "delete"],
    "LIST_CONTEXT_ACTIONS": ["parent", "filter", "create"],
    "DETAIL_CONTEXT_ACTIONS": ["home", "update", "delete"],
    "CREATE_CONTEXT_ACTIONS": ["home"],
    "UPDATE_CONTEXT_ACTIONS": ["home"],
    "DELETE_CONTEXT_ACTIONS": ["home"],
}
```

See [references/api-reference.md](references/api-reference.md) for full settings and all ViewSet/view attributes.

---

## Formsets (Inline Child Records)

Use `FormSetMixin` on Create/Update views to manage nested inline formsets. Configure with `cv_formsets`.

```python
from crud_views.lib.formsets import FormSet, FormSets, FormSetMixin, InlineFormSet
from crispy_forms.layout import Row

class ItemFormSet(InlineFormSet):
    model = Item
    parent_model = Order
    fk_name = "order"
    fields = ["name", "quantity", "price"]
    extra = 1

    def get_helper_layout_fields(self):
        return [Row(Column4("name"), Column4("quantity"), Column4("price"))]

class OrderCreateView(FormSetMixin, CrispyModelViewMixin, CreateViewPermissionRequired):
    cv_viewset = cv_order
    form_class = OrderCreateForm
    cv_formsets = FormSets(formsets={
        "items": FormSet(
            klass=ItemFormSet,
            title="Order Items",
            fields=["name", "quantity", "price"],
            pk_field="id",
        )
    })
```

---

## Polymorphic Models (`crud_views_polymorphic`)

Two-step create flow for polymorphic models (requires `django-polymorphic`).

Install: `pip install django-crud-views[polymorphic]`, add `"crud_views_polymorphic.apps.CrudViewsPolymorphicConfig"` to `INSTALLED_APPS`.

```python
from crud_views_polymorphic.lib import (
    PolymorphicCreateSelectViewPermissionRequired,  # step 1: choose subtype
    PolymorphicCreateViewPermissionRequired,         # step 2: fill subtype form
    PolymorphicUpdateViewPermissionRequired,
    PolymorphicDetailViewPermissionRequired,
)
from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm
from crud_views_polymorphic.lib.delete import PolymorphicDeleteViewPermissionRequired

class VehicleCreateSelectView(CrispyModelViewMixin, PolymorphicCreateSelectViewPermissionRequired):
    form_class = PolymorphicContentTypeForm
    cv_viewset = cv_vehicle
    # cv_polymorphic_include = [Car, Truck]  # optional whitelist
    # cv_polymorphic_exclude = [...]         # optional blacklist (mutually exclusive)

class VehicleCreateView(CrispyModelViewMixin, PolymorphicCreateViewPermissionRequired):
    cv_viewset = cv_vehicle
    polymorphic_forms = {Car: CarForm, Truck: TruckForm}

class VehicleUpdateView(CrispyModelViewMixin, PolymorphicUpdateViewPermissionRequired):
    cv_viewset = cv_vehicle
    polymorphic_forms = {Car: CarForm, Truck: TruckForm}

class VehicleDeleteView(CrispyModelViewMixin, PolymorphicDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_vehicle

class VehicleDetailView(PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_vehicle
    cv_property_display = [
        {"title": "Attributes", "properties": ["name"]},
    ]
```

List view must use `cv_context_actions = ["create_select"]` instead of `"create"`.

---

## WorkflowView (FSM State Transitions)

Integrates django-fsm-2 state machines with the CRUD framework. Provides transition execution, comment requirements, and a full audit log.

Full reference: see [references/workflow.md](references/workflow.md)

### Quick pattern

```python
# 1. Model: mix in WorkflowModelMixin, define states and @transition methods
from django.db import models
from django_fsm import FSMField, transition
from crud_views_workflow.lib.enums import WorkflowComment, BadgeEnum
from crud_views_workflow.lib.mixins import WorkflowModelMixin

class CampaignState(models.TextChoices):
    NEW = "new", "New"
    ACTIVE = "active", "Active"
    DONE = "done", "Done"

class Campaign(WorkflowModelMixin, models.Model):
    STATE_CHOICES = CampaignState
    STATE_BADGES = {
        CampaignState.NEW: BadgeEnum.LIGHT,
        CampaignState.ACTIVE: BadgeEnum.INFO,
        CampaignState.DONE: BadgeEnum.SUCCESS,
    }
    STATE_BADGE_DEFAULT = BadgeEnum.SECONDARY  # fallback for unmapped states
    COMMENT_DEFAULT = WorkflowComment.NONE     # fallback when custom["comment"] omitted
    state = FSMField(default=CampaignState.NEW, choices=CampaignState.choices)

    @transition(field=state, source=CampaignState.NEW, target=CampaignState.ACTIVE,
                on_error=CampaignState.DONE,
                custom={"label": "Activate", "comment": WorkflowComment.NONE})
    def wf_activate(self, request=None, by=None, comment=None):
        pass

    @transition(field=state, source=CampaignState.NEW, target=CampaignState.DONE,
                on_error=CampaignState.DONE,
                custom={"label": "Complete", "comment": WorkflowComment.REQUIRED})
    def wf_complete(self, request=None, by=None, comment=None):
        pass

# 2. Form
from crud_views_workflow.lib.forms import WorkflowForm
class CampaignWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = Campaign

# 3. View
from crud_views_workflow.lib.views import WorkflowViewPermissionRequired
class CampaignWorkflowView(CrispyModelViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_context_actions = ["list", "detail", "workflow"]
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm

    def on_transition(self, info, transition, state_old, state_new, comment, user, data):
        # optional hook: runs after each successful transition
        pass
```

WorkflowComment values: `NONE` (hidden), `OPTIONAL` (shown, not required), `REQUIRED` (shown, mandatory).

Install: `pip install django-crud-views[workflow]`, add `"crud_views_workflow.apps.CrudViewsWorkflowConfig"` to `INSTALLED_APPS`, run `migrate`.

---

## Per-Object Permissions (`crud_views_guardian`)

Integrates [django-guardian](https://django-guardian.readthedocs.io/) for per-object permission checking and queryset filtering. Swap `ViewSet` → `GuardianViewSet` and `*ViewPermissionRequired` → `Guardian*ViewPermissionRequired`.

Install: `pip install django-crud-views[guardian]`, add `"guardian"` and `"crud_views_guardian.apps.CrudViewsGuardianConfig"` to `INSTALLED_APPS`, add `"guardian.backends.ObjectPermissionBackend"` to `AUTHENTICATION_BACKENDS`, set `ANONYMOUS_USER_NAME = None`, run `migrate`.

```python
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)

cv_author = GuardianViewSet(model=Author, name="author")

class AuthorListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_author

class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
```

### Assigning permissions

```python
cv_author.assign_perm("view", user, author_instance)   # grant
cv_author.remove_perm("view", user, author_instance)   # revoke
cv_author.assign_perm("change", group, author_instance)
qs = cv_author.get_objects_for_user(user, "view")
```

### Strict mode (default)

`cv_guardian_accept_global_perms = False` by default — model-level Django permissions are **not** a fallback. Only explicit per-object grants count. Override per view:

```python
class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_guardian_accept_global_perms = True  # allow model-level perms as fallback
```

### Create views

- **Top-level creates** (no parent): standard model-level `add_<model>` permission is checked.
- **Child creates** (with parent viewset): guardian checks per-object permission on the parent using `cv_guardian_parent_create_permission`.

### Parent viewsets

```python
cv_book = GuardianViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    cv_guardian_parent_permission="view",           # for list/detail/update/delete
    cv_guardian_parent_create_permission="change",  # for create (None = use above)
)
```

Setting either to `None` disables the parent check for that view type.