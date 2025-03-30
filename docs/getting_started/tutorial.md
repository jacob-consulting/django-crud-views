# Tutorial

This tutorial will show you the features of Django CRUD Views.

> **Note:** Basic Django knowledge such as creating a Python environment with a Django project and a Django app is
> required. See the [Django Tutorial](https://docs.djangoproject.com/en/3.2/intro/tutorial01/) for more information.


## Django Model

Create a Django model, i.e. for an author:

```python
from django.db import models

class Author(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    pseudonym = models.CharField(max_length=100, blank=True, null=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)
```

## ViewSet

Next create a ViewSet:

```python
from crud_views.lib.viewset import ViewSet, path_regs
from .models import Author

vs_author = ViewSet(
    model=Author,
    name="author",
    pk=path_regs.UUID,  # regexp for the primary key in the URL-routing  (defaults to integer)
    icon_header="fa-regular fa-user"  # when using boostrap5 with font-awsome
)
```

> **Note:** A `ViewSet` is the container for all views that belong to it. It configures the routers for all these views and helps the views to link to their sibling views.  


## Urls

Add the ViewSet's urlpattern to your app:

```python
from app.views.author import vs_author

urlpatterns = [
    # your other urlpatterns
]

# add the ViewSet's urlpatterns
urlpatterns += vs_author.urlpatterns
```

> **Note:** `ViewSet` creates routers for each `CrudView` of the ViewSet.  

## The List View

Create a list view with a table based on [django-tables2](https://django-tables2.readthedocs.io/en/latest/)

```python
from crud_views.lib.table import Table
from crud_views.lib.views import ListViewTableMixin, ListViewPermissionRequired

class AuthorTable(Table):
    id = UUIDLinkDetailColumn()
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column()
    created_dt = NaturalDayColumn()
    modified_dt = NaturalTimeColumn()

    
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Author
    table_class = AuthorTable   # set the table class
    vs = vs_author  # this will attach your list view to the ViewSet
```

> **Notes:** 
> 
> - `Table` is from `django-tables2`.
> - `ListViewPermissionRequired` implements Django's `generic.ListView` and `mixins.PermissionRequiredMixin`.
> - `ListViewTableMixin` extends `SingleTableMixin` which passes the view to the Table constructor. 
>
> So everything is as close to Django's generic classes as possible.

Now create a model:

```bash
alex@inifinity:~/django-crud-views/examples/bootstrap5$ task shell
>>> from app.models import Author
>>> Author.objects.create(first_name="Douglas", last_name="Adams", pseudonym="DS")
<Author: Douglas Adams>
```

Then go to `http://localhost:8000/author/` and you will see the list view of the authors.

![list](assets/list.png)
