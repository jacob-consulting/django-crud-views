import django_tables2 as tables

import django_filters

from django.forms import modelform_factory
from django.forms.fields import CharField

from django.core.exceptions import ValidationError

from tests.test1.app.models import Author, Publisher, Book, Vehicle, Car, Truck, Campaign
from crud_views.lib.crispy import CrispyModelViewMixin, CrispyDeleteForm, CrispyModelForm
from crud_views.lib.crispy.form import CrispyForm
from crud_views.lib.table import Table, UUIDLinkDetailColumn, LinkDetailColumn
from crud_views.lib.views import (
    ListViewTableMixin,
    ListViewTableFilterMixin,
    MessageMixin,
    ListViewPermissionRequired,
    DeleteViewPermissionRequired,
    CreateViewPermissionRequired,
    UpdateViewPermissionRequired,
    DetailViewPermissionRequired,
    CreateViewParentMixin,
    OrderedUpViewPermissionRequired,
    OrderedUpDownPermissionRequired,
    CardListViewPermissionRequired,
    DetailCustomViewPermissionRequired,
    ActionViewPermissionRequired,
)
from crud_views.lib.view import CardAction
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.views.manage import ManageView
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views_polymorphic.lib import (
    PolymorphicCreateViewPermissionRequired,
    PolymorphicCreateSelectViewPermissionRequired,
    PolymorphicUpdateViewPermissionRequired,
    PolymorphicDetailViewPermissionRequired,
)
from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm
from crud_views_polymorphic.lib.delete import PolymorphicDeleteViewPermissionRequired
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default
from crud_views.lib.view import ContextButton, ParentContextButton
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianCardListViewPermissionRequired,
)
from crud_views_workflow.lib.forms import WorkflowForm
from crud_views_workflow.lib.views import WorkflowViewPermissionRequired
from crud_views.lib.crispy import Column4, Column6, Column12
from crispy_forms.layout import Row, Layout

cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")


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
        "update",
        "delete",  # "up", "down", "redirect_child"
    ]


class AuthorCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_author
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
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


class AuthorPingView(ActionViewPermissionRequired):
    cv_key = "ping"
    cv_path = "ping"
    cv_viewset = cv_author
    cv_backend_only = True
    cv_message_template_code = "Pinged »{{ object }}«"
    cv_message_template_error_code = "Ping failed for »{{ object }}«"

    def action(self, context):
        # result controllable from the request for testing both branches
        return self.request.GET.get("fail") != "1"


class AuthorSilentPingView(ActionViewPermissionRequired):
    cv_key = "ping_silent"
    cv_path = "ping-silent"
    cv_viewset = cv_author
    cv_backend_only = True

    def action(self, context):
        return True


class AuthorMutedPingView(ActionViewPermissionRequired):
    cv_key = "ping_muted"
    cv_path = "ping-muted"
    cv_viewset = cv_author
    cv_backend_only = True
    cv_action_messages = False
    cv_message_template_code = "Should not appear"

    def action(self, context):
        return True


class AuthorHookPingView(ActionViewPermissionRequired):
    cv_key = "ping_hook"
    cv_path = "ping-hook"
    cv_viewset = cv_author
    cv_backend_only = True

    def action(self, context):
        return True

    def cv_action_success_hook(self, context):
        self.object.pseudonym = "hooked"
        self.object.save()


class AuthorContactForm(CrispyModelForm):
    from django.forms.fields import CharField as _CharField

    subject = _CharField(label="Subject", required=True)
    body = _CharField(label="Body", required=True)

    class Meta:
        model = Author
        fields = ["subject", "body"]

    def get_layout_fields(self):
        from crud_views.lib.crispy import Column12

        return Column12("subject"), Column12("body")


class AuthorContactView(CrispyModelViewMixin, MessageMixin, CustomFormViewPermissionRequired):
    cv_key = "contact"
    cv_path = "contact"
    cv_viewset = cv_author
    form_class = AuthorContactForm
    cv_message_template_code = "Contacted author »{{ object }}«"
    cv_header_template_code = "Contact Author"
    cv_paragraph_template_code = "Send a message to the Author"

    def cv_form_valid(self, context):
        pass


# --- Author Wide Card (custom cv_card_container_class) ---

cv_author_wide_card = ViewSet(model=Author, name="author_wide_card")


class AuthorWideCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_author_wide_card
    cv_card_container_class = "col-md-12"
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
    ]


class AuthorWideCardDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author_wide_card


class AuthorWideCardCreateView(CrispyModelViewMixin, CreateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_author_wide_card


# --- Author Custom Detail (DetailCustomView without ObjectDetailMixin) ---

cv_author_custom_detail = ViewSet(model=Author, name="author_custom_detail")


class AuthorCustomDetailListView(ListViewPermissionRequired):
    cv_viewset = cv_author_custom_detail


class AuthorCustomDetailView(DetailCustomViewPermissionRequired):
    cv_viewset = cv_author_custom_detail
    template_name = "app/author_detail_custom.html"


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
    name = django_filters.CharFilter(lookup_expr="icontains")

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


class PublisherCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_publisher
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(child_name="book", child_key="list", label="Books"),
    ]


# --- Publisher Order Demo (card with ordering, paging, filter) ---

cv_publisher_order = ViewSet(
    model=Publisher,
    name="publisher_order",
)


class PublisherOrderFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Publisher
        fields = ["name"]


class PublisherOrderCardListView(ListViewTableFilterMixin, CardListViewPermissionRequired):
    cv_viewset = cv_publisher_order
    cv_order_fields = ["name", ("id", "ID")]
    cv_order_default = "-name"
    paginate_by = 2
    filterset_class = PublisherOrderFilter
    formhelper_class = PublisherFilterFormHelper
    cv_card_actions = []


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


# --- Contract (second child of publisher, sibling of book) ---

from tests.test1.app.models import Contract  # noqa: E402

cv_contract = ViewSet(
    model=Contract,
    name="contract",
    parent=ParentViewSet(name="publisher"),
    icon_header="fa-solid fa-file-contract",
)


class ContractTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()


class ContractListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = ContractTable
    cv_viewset = cv_contract
    cv_list_actions = ["detail"]


class ContractDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_contract
    cv_property_display = [
        {
            "title": "Attributes",
            "properties": ["title"],
        },
    ]


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


# Guardian viewsets for guardian integration tests

cv_guardian_author = GuardianViewSet(
    model=Author,
    name="guardian_author",
    icon_header="fa-regular fa-user",
)


class GuardianAuthorListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_guardian_author
    cv_list_actions = ["detail", "update", "delete"]


class GuardianAuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_guardian_author


class GuardianAuthorCreateView(CrispyModelViewMixin, GuardianCreateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_guardian_author


class GuardianAuthorUpdateView(CrispyModelViewMixin, GuardianUpdateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_guardian_author


class GuardianAuthorDeleteView(CrispyModelViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_guardian_author


class GuardianAuthorCardListView(GuardianCardListViewPermissionRequired):
    cv_viewset = cv_guardian_author
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
    ]


cv_guardian_publisher = GuardianViewSet(
    model=Publisher,
    name="guardian_publisher",
    icon_header="fa-regular fa-building",
)


class GuardianPublisherListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_guardian_publisher
    cv_list_actions = ["detail", "update", "delete"]


class GuardianPublisherDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_guardian_publisher


class GuardianPublisherCreateView(CrispyModelViewMixin, GuardianCreateViewPermissionRequired):
    form_class = PublisherForm
    cv_viewset = cv_guardian_publisher


class GuardianPublisherUpdateView(CrispyModelViewMixin, GuardianUpdateViewPermissionRequired):
    form_class = PublisherForm
    cv_viewset = cv_guardian_publisher


class GuardianPublisherDeleteView(CrispyModelViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_guardian_publisher


cv_guardian_book = GuardianViewSet(
    model=Book,
    name="guardian_book",
    parent=ParentViewSet(name="guardian_publisher", attribute="publisher"),
    icon_header="fa-regular fa-address-book",
    cv_guardian_parent_permission="view",
    cv_guardian_parent_create_permission="change",
    context_buttons=context_buttons_default()
    + [
        ContextButton(key="create_button", key_target="create"),  # key != key_target
        ParentContextButton(key="publisher_detail", key_target="detail"),  # → object-gated parent detail
        ParentContextButton(
            key="publisher_detail_labeled", key_target="detail", label_template_code="Publisher Home"
        ),  # → parent detail with a custom label
    ],
)


class GuardianBookListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    table_class = BookTable
    cv_viewset = cv_guardian_book
    cv_list_actions = ["detail", "update", "delete"]


class GuardianBookDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_guardian_book


class GuardianBookCreateView(CrispyModelViewMixin, CreateViewParentMixin, GuardianCreateViewPermissionRequired):
    form_class = BookForm
    cv_viewset = cv_guardian_book


class GuardianBookUpdateView(CrispyModelViewMixin, GuardianUpdateViewPermissionRequired):
    form_class = BookForm
    cv_viewset = cv_guardian_book


class GuardianBookDeleteView(CrispyModelViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_guardian_book


# --- Guardian Publisher Cascade (INT PK, Guardian + cv_show_related_objects=True) ---

cv_guardian_publisher_cascade = GuardianViewSet(
    model=Publisher,
    name="guardian_publisher_cascade",
    icon_header="fa-regular fa-building",
)


class GuardianPublisherCascadeListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_guardian_publisher_cascade


class GuardianPublisherCascadeDeleteView(CrispyModelViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_guardian_publisher_cascade
    cv_show_related_objects = True


# --- Publisher Cascade (INT PK, cv_show_related_objects=True) ---

cv_publisher_cascade = ViewSet(
    model=Publisher,
    name="publisher_cascade",
)


class PublisherCascadeListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_cascade


class PublisherCascadeDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher_cascade
    cv_show_related_objects = True


# --- Publisher Protected (INT PK, cv_check_delete_protection hook) ---

cv_publisher_protected = ViewSet(
    model=Publisher,
    name="publisher_protected",
)


class PublisherProtectedListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_protected


class PublisherProtectedDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher_protected
    cv_show_related_objects = True

    def cv_check_delete_protection(self) -> list[str]:
        return ["Cannot delete this publisher."]


# --- Publisher Form Protected (INT PK, form clean() blocks deletion) ---

cv_publisher_form_protected = ViewSet(
    model=Publisher,
    name="publisher_form_protected",
)


class ProtectedDeleteForm(CrispyDeleteForm):
    def clean(self):
        cleaned_data = super().clean()
        raise ValidationError("Form-level protection: cannot delete.")
        return cleaned_data


class PublisherFormProtectedDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    form_class = ProtectedDeleteForm
    cv_viewset = cv_publisher_form_protected


class PublisherFormProtectedListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_form_protected


# --- Publisher Linked (INT PK, cv_link_related_objects=True) ---

cv_publisher_linked = ViewSet(
    model=Publisher,
    name="publisher_linked",
)


class PublisherLinkedListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_linked


class PublisherLinkedDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher_linked
    cv_show_related_objects = True
    cv_link_related_objects = True


# ── Test helpers ──────────────────────────────────────────────────────────────


class CustomManageViewForTest(ManageView):
    """Importable subclass used by test_manage.py to verify manage_view_class."""

    pass


class CustomGuardianManageViewForTest(ManageView):
    """Importable subclass used by test_guardian.py to verify manage_view_class on GuardianViewSet."""

    pass


# --- Author Modal (UUID PK, cv_modal=True on delete/detail/custom form) ---

cv_author_modal = ViewSet(
    model=Author,
    name="author_modal",
)


class AuthorModalListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author_modal


class AuthorModalDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author_modal
    cv_modal = True
    cv_property_display = [
        {"title": "Attributes", "properties": ["first_name", "last_name"]},
    ]


class AuthorModalDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author_modal
    cv_modal = True
    cv_modal_size = "modal-lg"


class AuthorModalContactForm(CrispyModelForm):
    submit_label = "Send"
    subject = CharField(label="Subject", required=True)
    body = CharField(label="Body", required=True)

    class Meta:
        model = Author
        fields = ["subject", "body"]

    def get_layout_fields(self):
        return Column12("subject"), Column12("body")


class AuthorModalContactView(MessageMixin, CrispyModelViewMixin, CustomFormViewPermissionRequired):
    cv_key = "contact"
    cv_path = "contact"
    cv_viewset = cv_author_modal
    cv_modal = True
    form_class = AuthorModalContactForm
    cv_icon_action = "fa-solid fa-envelope"
    cv_message_template_code = "Contacted author"
    cv_header_template_code = "Contact"
    cv_paragraph_template_code = "Contact the author"
    cv_action_label_template_code = "Contact"
    cv_action_short_label_template_code = "Contact"


# --- Publisher Modal Protected (INT PK, cv_modal + delete protection) ---

cv_publisher_modal_protected = ViewSet(
    model=Publisher,
    name="publisher_modal_protected",
)


class PublisherModalProtectedListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = PublisherTable
    cv_viewset = cv_publisher_modal_protected


class PublisherModalProtectedDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher_modal_protected
    cv_modal = True

    def cv_check_delete_protection(self) -> list[str]:
        return ["Cannot delete this publisher."]
