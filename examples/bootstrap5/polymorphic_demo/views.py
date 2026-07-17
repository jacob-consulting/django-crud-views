import django_tables2 as tables
from crispy_forms.layout import Row
from django.forms import modelform_factory

from crud_views.lib.crispy import Column4, Column6, CrispyDeleteForm, CrispyForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import ListViewPermissionRequired, ListViewTableMixin
from crud_views.lib.viewset import ViewSet
from crud_views_polymorphic.lib import (
    PolymorphicCreateSelectViewPermissionRequired,
    PolymorphicCreateViewPermissionRequired,
    PolymorphicDetailViewPermissionRequired,
    PolymorphicUpdateViewPermissionRequired,
)
from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm
from crud_views_polymorphic.lib.delete import PolymorphicDeleteViewPermissionRequired

from polymorphic_demo.models import Car, Motorcycle, Truck, Vehicle

cv_vehicle = ViewSet(model=Vehicle, name="vehicle", icon_header="fa-solid fa-car")


def _typed_form(model, extra_field):
    base = modelform_factory(model, fields=["name", extra_field])

    class TypedForm(CrispyForm, base):
        def get_layout_fields(self):
            return (Row(Column6("name"), Column6(extra_field)),)

    return TypedForm


CarForm = _typed_form(Car, "doors")
TruckForm = _typed_form(Truck, "payload_tons")
MotorcycleForm = _typed_form(Motorcycle, "engine_cc")

POLYMORPHIC_FORMS = {Car: CarForm, Truck: TruckForm, Motorcycle: MotorcycleForm}


class VehicleTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    type = tables.Column(accessor="polymorphic_ctype__model", verbose_name="Type")


class VehicleListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_vehicle
    table_class = VehicleTable
    cv_list_actions = ["detail", "update", "delete"]
    cv_context_actions = ["create_select"]


class CrispyVehicleContentTypeForm(CrispyForm, PolymorphicContentTypeForm):
    submit_label = "Select"

    def get_layout_fields(self):
        return Row(Column4("polymorphic_ctype_id"))


class VehicleCreateSelectView(CrispyViewMixin, PolymorphicCreateSelectViewPermissionRequired):
    cv_viewset = cv_vehicle
    model = Vehicle
    form_class = CrispyVehicleContentTypeForm


class VehicleCreateView(CrispyViewMixin, PolymorphicCreateViewPermissionRequired):
    cv_viewset = cv_vehicle
    model = Vehicle
    cv_context_actions = ["home"]
    polymorphic_forms = POLYMORPHIC_FORMS


class VehicleUpdateView(CrispyViewMixin, PolymorphicUpdateViewPermissionRequired):
    cv_viewset = cv_vehicle
    model = Vehicle
    polymorphic_forms = POLYMORPHIC_FORMS


class VehicleDetailView(PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_vehicle
    model = Vehicle
    cv_property_display = [
        {"title": "Vehicle", "icon": "car", "properties": ["id", "name"]},
    ]


class VehicleDeleteView(CrispyViewMixin, PolymorphicDeleteViewPermissionRequired):
    cv_viewset = cv_vehicle
    model = Vehicle
    form_class = CrispyDeleteForm
