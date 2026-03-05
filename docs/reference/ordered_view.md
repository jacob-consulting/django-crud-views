# OrderedView

The `OrderedUpView` and `OrderedDownView` integrate [django-ordered-model](https://github.com/django-ordered-model/django-ordered-model)
with the crud-views framework. They provide up/down reordering actions for model instances that
extend `OrderedModel`.

## Installation

Install the `ordered` optional dependency group:

```bash
pip install django-crud-views[ordered]
```

## Model

Your model must extend `OrderedModel`:

```python
from ordered_model.models import OrderedModel

class Author(OrderedModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta(OrderedModel.Meta):
        pass
```

Add `ordered_model` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "ordered_model",
]
```

## Views

```python
from crud_views.lib.views import (
    OrderedUpViewPermissionRequired,
    OrderedUpDownPermissionRequired,
)

class AuthorUpView(OrderedUpViewPermissionRequired):
    cv_viewset = cv_author


class AuthorDownView(OrderedUpDownPermissionRequired):
    cv_viewset = cv_author
```

## List View Integration

Add `"up"` and `"down"` to `cv_list_actions` to show the reordering buttons per row:

```python
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete", "up", "down"]
```

## View Classes

| Class | Description |
|-------|-------------|
| `OrderedUpView` | Moves the instance up in order (no permission check) |
| `OrderedUpViewPermissionRequired` | Same, requires `change` permission |
| `OrderedDownView` | Moves the instance down in order (no permission check) |
| `OrderedUpDownPermissionRequired` | Same, requires `change` permission |
