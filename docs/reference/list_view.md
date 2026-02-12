# ListView

The `ListView` displays a list of model instances. It integrates with
[django-tables2](https://django-tables2.readthedocs.io/en/latest/) for table rendering and
[django-filter](https://django-filter.readthedocs.io/en/stable/) for filtering.

## Basic Usage

A minimal list view with a table:

```python
import django_tables2 as tables
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.views import ListViewTableMixin, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from .models import Author

cv_author = ViewSet(
    model=Author,
    name="author",
    icon_header="fa-regular fa-user",
)


class AuthorTable(Table):
    id = UUIDLinkDetailColumn()
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column()


class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author
```

## View Classes

| Class | Description |
|-------|-------------|
| `ListView` | Base list view without permission checks |
| `ListViewPermissionRequired` | List view with `view` permission required |

Both inherit from Django's `generic.ListView` and `CrudView`.

## Configuration

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Model` | from `cv_viewset` | The Django model to list (auto-derived from ViewSet) |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_list_actions` | `list[str]` | `["detail", "update", "delete"]` | Actions shown per row in the table |
| `cv_context_actions` | `list[str]` | `["parent", "filter", "create"]` | Actions shown in the header area |
| `paginate_by` | `int` | `10` | Number of items per page |

### Customizing List Actions

Control which action buttons appear per row:

```python
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete", "up", "down"]
```

## Table with django-tables2

Use `ListViewTableMixin` to render the list as a table. Define a table class
using `Table` (which extends django-tables2's `Table`):

```python
import django_tables2 as tables
from crud_views.lib.table import Table, UUIDLinkDetailColumn, LinkChildColumn
from crud_views.lib.table.columns import NaturalTimeColumn, NaturalDayColumn


class AuthorTable(Table):
    id = UUIDLinkDetailColumn(attrs=Table.ca.ID)
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column(attrs=Table.ca.w20)
    books = LinkChildColumn(name="book", verbose_name="Books", attrs=Table.ca.w10)
    created_dt = NaturalDayColumn()
    modified_dt = NaturalTimeColumn()
```

### Column Types

| Column | Description |
|--------|-------------|
| `UUIDLinkDetailColumn` | UUID primary key rendered as a link to the detail view |
| `LinkDetailColumn` | Integer primary key rendered as a link to the detail view |
| `LinkChildColumn` | Link to a child ViewSet's list view |
| `NaturalDayColumn` | Date rendered as natural day (e.g. "today", "yesterday") |
| `NaturalTimeColumn` | DateTime rendered as natural time (e.g. "2 hours ago") |

## Filtering with django-filter

Add `ListViewTableFilterMixin` and configure a filter set and form helper:

```python
import django_filters
from crispy_forms.layout import Layout, Row
from crud_views.lib.crispy import Column4
from crud_views.lib.views import ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired
from crud_views.lib.views.list import ListViewFilterFormHelper


class AuthorFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(
        Row(
            Column4("first_name"), Column4("last_name")
        ),
    )


class AuthorFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Author
        fields = ["first_name", "last_name"]


class AuthorListView(ListViewTableMixin,
                     ListViewTableFilterMixin,
                     ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author

    # filter config
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper
```

### Filter Persistence

Filter values are stored in the user session by default, so the filter state is preserved
when navigating away and back. Control this with:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `cv_filter_persistence` | `bool` | `True` | Store filter state in session |

This can also be configured globally via the `FILTER_PERSISTENCE` setting.
