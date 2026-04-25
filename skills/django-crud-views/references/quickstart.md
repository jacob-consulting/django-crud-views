# django-crud-views Quick Start

## 1. Define the ViewSet

```python
# views/author.py
from crud_views.lib.viewset import ViewSet
from .models import Author

cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")
```

## 2. Add URL patterns

```python
# urls.py
from app.views.author import cv_author

urlpatterns += cv_author.urlpatterns
```

## 3. List view with table

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

## 4. Create / Update views

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

## 5. Delete view

```python
from crud_views.lib.crispy import CrispyDeleteForm
from crud_views.lib.views import DeleteViewPermissionRequired

class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message = "Deleted author »{object}«"
```

## 6. Detail view

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
