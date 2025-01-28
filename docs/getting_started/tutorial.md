# Tutorial

This tutorial will show you the features of Django CRUD Views.

> **Note:** Basic Django knowledge such as creating a Python environment with a Django project and a Django app is
> required.

Create a Django Model, i.e. for an Author:

```python
class Author(OrderedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    pseudonym = models.CharField(max_length=100, blank=True, null=True)
```

Next create a ViewSet:

```python
from crud_views.lib.viewset import ViewSet, path_regs

vs_author = ViewSet(
    model=Author,
    name="author",
    pk=path_regs.UUID,  # specify if it is not an integer which is the default
    icon_header="fa-regular fa-user"  # when using boostrap5 with font-awsome
)
```

> **Note:** A `ViewSet` is the container for all views that belong to it. It configures the routers for all these views and helps the views to link to their sibling views.  

Add the ViewSet's urlpattern to your app:

```python
from app.views.author import vs_author

urlpatterns = [
    # your other urlpatterns
]

# add the ViewSet's urlpatterns
urlpatterns += vs_author.urlpatterns
```

> **Note:** `ViewSet` creates routers for each `ViewSetView` of the ViewSet.  

Create a list view with a table based on [django-tables2](https://django-tables2.readthedocs.io/en/latest/)

```python
from crud_views.lib.table import Table
from crud_views.lib.views import ListViewTableMixin, ListViewPermissionRequired


class AuthorTable(Table):
    id = UUIDLinkDetailColumn()
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column()

class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Author
    table_class = AuthorTable
    vs = vs_author  # this will link your list view to the ViewSet
```

> **Notes:** 
> 
> - `Table` is built on `django-tables2` `Table`. It adds the view to the table.
> - `ListViewPermissionRequired` is built on Django's `generic.ListView` and `mixins.PermissionRequiredMixin`
> - `ListViewTableMixin` extends `SingleTableMixin` which passes the view to the Table constructor. 
>
> So everything is is as close to the Django classes as possible.

Add a record via Django Admin and open your Browser to see the result:

![author.png](assets/author.png)
