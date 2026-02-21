# PolymorphicView

The `crud_views_polymorphic` package adds support for [django-polymorphic](https://django-polymorphic.readthedocs.io/en/stable/)
models. It provides a two-step create flow (select subtype → fill form) and polymorphic-aware
detail, update, and delete views that resolve the correct form based on the actual subtype of
each object.

## Installation

Install the `polymorphic` optional dependency group:

```bash
pip install django-crud-views[polymorphic]
```

Add the required apps to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "polymorphic",
    "crud_views_polymorphic.apps.CrudViewsPolymorphicConfig",
    ...
]
```

## Basic Usage

### 1. Define the model

Inherit from `PolymorphicModel` for the base class and define concrete subtypes:

```python
from django.db import models
from polymorphic.models import PolymorphicModel


class Vehicle(PolymorphicModel):
    name = models.CharField(max_length=128)


class Car(Vehicle):
    doors = models.IntegerField()


class Truck(Vehicle):
    payload_tons = models.FloatField()
```

### 2. Define the ViewSet and views

```python
from django.forms import modelform_factory

from crud_views.lib.viewset import ViewSet
from crud_views.lib.crispy import CrispyModelViewMixin
from crud_views.lib.crispy.form import CrispyDeleteForm
from crud_views_polymorphic.lib import (
    PolymorphicCreateViewPermissionRequired,
    PolymorphicCreateSelectViewPermissionRequired,
    PolymorphicUpdateViewPermissionRequired,
    PolymorphicDetailViewPermissionRequired,
)
from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm
from crud_views_polymorphic.lib.delete import PolymorphicDeleteViewPermissionRequired

from .models import Vehicle, Car, Truck

cv_vehicle = ViewSet(model=Vehicle, name="vehicle")

CarForm = modelform_factory(Car, fields=["name", "doors"])
TruckForm = modelform_factory(Truck, fields=["name", "payload_tons"])


class VehicleCreateSelectView(CrispyModelViewMixin, PolymorphicCreateSelectViewPermissionRequired):
    form_class = PolymorphicContentTypeForm
    cv_viewset = cv_vehicle


class VehicleCreateView(CrispyModelViewMixin, PolymorphicCreateViewPermissionRequired):
    cv_viewset = cv_vehicle
    polymorphic_forms = {
        Car: CarForm,
        Truck: TruckForm,
    }


class VehicleUpdateView(CrispyModelViewMixin, PolymorphicUpdateViewPermissionRequired):
    cv_viewset = cv_vehicle
    polymorphic_forms = {
        Car: CarForm,
        Truck: TruckForm,
    }


class VehicleDeleteView(CrispyModelViewMixin, PolymorphicDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_vehicle


class VehicleDetailView(PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_vehicle
    cv_property_display = [
        {"title": "Attributes", "properties": ["name"]},
    ]
```

### 3. Register URLs

```python
# urls.py
urlpatterns = cv_vehicle.urlpatterns
```

### 4. Add the create_select action to the list view

```python
from crud_views.lib.views import ListViewPermissionRequired, ListViewTableMixin

class VehicleListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_vehicle
    cv_list_actions = ["detail", "update", "delete"]
    cv_context_actions = ["create_select"]
```

## View Classes

| Class | Permission |
|-------|-----------|
| `PolymorphicCreateSelectView` | — |
| `PolymorphicCreateSelectViewPermissionRequired` | `add` |
| `PolymorphicCreateView` | — |
| `PolymorphicCreateViewPermissionRequired` | `add` |
| `PolymorphicUpdateView` | — |
| `PolymorphicUpdateViewPermissionRequired` | `change` |
| `PolymorphicDeleteView` | — |
| `PolymorphicDeleteViewPermissionRequired` | `delete` |
| `PolymorphicDetailView` | — |
| `PolymorphicDetailViewPermissionRequired` | `view` |

## Two-step create flow

Creating a polymorphic instance requires two steps:

1. **`create_select`** — `PolymorphicCreateSelectView` renders a form with a `ChoiceField` of all
   registered subtypes. On submit it redirects to the `create` URL, passing `polymorphic_ctype_id`
   as a URL parameter.

2. **`create`** — `PolymorphicCreateView` reads `polymorphic_ctype_id` from the URL, resolves the
   subtype model via the content-type framework, and renders the matching form from `polymorphic_forms`.

### Filtering available subtypes

`PolymorphicCreateSelectView` supports filtering which subtypes appear in the select form:

| Attribute | Type | Description |
|-----------|------|-------------|
| `cv_polymorphic_exclude` | `list[type]` or `None` | Subtypes to hide from the select form |
| `cv_polymorphic_include` | `list[type]` or `None` | Only these subtypes appear in the select form |

Only one of the two may be set at a time (enforced by system check `E220`).

## `polymorphic_forms`

Set `polymorphic_forms` on `PolymorphicCreateView` and `PolymorphicUpdateView` to a dict that maps
each subtype model class to its form class:

```python
polymorphic_forms = {
    Car: CarForm,
    Truck: TruckForm,
}
```

The correct form is selected at runtime based on the resolved subtype.

## System checks

| ID | View | What is checked |
|----|------|----------------|
| `E220` | `PolymorphicCreateSelectView` | At most one of `cv_polymorphic_exclude` / `cv_polymorphic_include` is set |
