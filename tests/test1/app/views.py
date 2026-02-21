import django_tables2 as tables

import django_filters

from django.forms import modelform_factory

from tests.test1.app.models import Author, Publisher, Book, Vehicle, Car, Truck, Campaign
from crud_views.lib.crispy import CrispyModelViewMixin, CrispyDeleteForm, CrispyModelForm
from crud_views.lib.crispy.form import CrispyForm
from crud_views.lib.table import Table, UUIDLinkDetailColumn, LinkDetailColumn
from crud_views.lib.views import (
    ListViewTableMixin, ListViewTableFilterMixin, MessageMixin,
    ListViewPermissionRequired, DeleteViewPermissionRequired, CreateViewPermissionRequired,
    UpdateViewPermissionRequired, DetailViewPermissionRequired, CreateViewParentMixin,
    OrderedUpViewPermissionRequired, OrderedUpDownPermissionRequired
)
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views_polymorphic.lib import (
    PolymorphicCreateViewPermissionRequired, PolymorphicCreateSelectViewPermissionRequired,
    PolymorphicUpdateViewPermissionRequired, PolymorphicDetailViewPermissionRequired
)
from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm
from crud_views_polymorphic.lib.delete import PolymorphicDeleteViewPermissionRequired
from crud_views.lib.viewset import ViewSet, ParentViewSet
from crud_views_workflow.lib.forms import WorkflowForm
from crud_views_workflow.lib.views import WorkflowViewPermissionRequired
from crud_views.lib.crispy import Column4, Column6
from crispy_forms.layout import Row, Layout

cv_author = ViewSet(
    model=Author,
    name="author",
    icon_header="fa-regular fa-user"
)


class AuthorTable(Table):
    id = UUIDLinkDetailColumn()
    first_name = tables.Column()
    last_name = tables.Column()
    pseudonym = tables.Column()


class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable

    cv_viewset = cv_author
    cv_list_actions = [
        "detail",
        "update", "delete",  # "up", "down", "redirect_child"
    ]


class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author

    cv_property_display = [
        {
            "title": "Attributes",
            "properties": [
                "full_name",
                "first_name",
                "last_name",
                "pseudonym",
            ],
        },
    ]


class AuthorForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorCreateView(CrispyModelViewMixin, CreateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_author


class AuthorUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_author


class AuthorDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author


class AuthorUpView(OrderedUpViewPermissionRequired):
    cv_viewset = cv_author


class AuthorDownView(OrderedUpDownPermissionRequired):
    cv_viewset = cv_author


# --- Publisher (INT PK) ---

cv_publisher = ViewSet(
    model=Publisher,
    name="publisher",
)


class PublisherTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class PublisherFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("name")))


class PublisherFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Publisher
        fields = ["name"]


class PublisherListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    filterset_class = PublisherFilter
    formhelper_class = PublisherFilterFormHelper
    cv_viewset = cv_publisher
    cv_list_actions = ["detail", "update", "delete"]


class PublisherDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_publisher
    cv_property_display = [
        {
            "title": "Attributes",
            "properties": ["name"],
        },
    ]


class PublisherForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Publisher
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class PublisherCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    form_class = PublisherForm
    cv_viewset = cv_publisher


class PublisherUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = PublisherForm
    cv_viewset = cv_publisher


class PublisherDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher


# --- Book (INT PK, child of Publisher) ---

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="publisher"),
)


class BookTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()


class BookListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = BookTable
    cv_viewset = cv_book
    cv_list_actions = ["detail", "update", "delete"]


class BookDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_property_display = [
        {
            "title": "Attributes",
            "properties": ["title"],
        },
    ]


class BookForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Book
        fields = ["title"]

    def get_layout_fields(self):
        return Row(Column4("title"))


class BookCreateView(CrispyModelViewMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    form_class = BookForm
    cv_viewset = cv_book


class BookUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    form_class = BookForm
    cv_viewset = cv_book


class BookDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_book


# --- Vehicle (polymorphic) ---

cv_vehicle = ViewSet(
    model=Vehicle,
    name="vehicle",
)


class VehicleTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class VehicleListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = VehicleTable
    cv_viewset = cv_vehicle
    cv_list_actions = ["detail", "update", "delete"]
    cv_context_actions = ["create_select"]


_CarForm = modelform_factory(Car, fields=["name", "doors"])


class CarForm(CrispyForm, _CarForm):
    def get_layout_fields(self):
        return Row(Column6("name"), Column6("doors"))


_TruckForm = modelform_factory(Truck, fields=["name", "payload_tons"])


class TruckForm(CrispyForm, _TruckForm):
    def get_layout_fields(self):
        return Row(Column6("name"), Column6("payload_tons"))


class CrispyVehicleContentTypeForm(CrispyForm, PolymorphicContentTypeForm):
    submit_label = "Select"

    def get_layout_fields(self):
        return Row(Column4("polymorphic_ctype_id"))


class VehicleCreateSelectView(CrispyModelViewMixin, PolymorphicCreateSelectViewPermissionRequired):
    form_class = CrispyVehicleContentTypeForm
    cv_viewset = cv_vehicle


class VehicleCreateView(CrispyModelViewMixin, PolymorphicCreateViewPermissionRequired):
    cv_viewset = cv_vehicle
    cv_context_actions = ["home"]
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
        {
            "title": "Attributes",
            "properties": ["name"],
        },
    ]


# --- Campaign (workflow) ---

cv_campaign = ViewSet(
    model=Campaign,
    name="campaign",
)


class CampaignTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    state = tables.Column(accessor="state_badge")


class CampaignListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_campaign
    cv_list_actions = ["detail", "workflow", "update", "delete"]
    table_class = CampaignTable


class CampaignDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_campaign
    cv_property_display = [
        {
            "title": "Attributes",
            "properties": ["name", "state"],
        },
    ]


class CampaignWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = Campaign


class CampaignWorkflowView(CrispyModelViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_context_actions = ["list", "detail", "workflow"]
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm
