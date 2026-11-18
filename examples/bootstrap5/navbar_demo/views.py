import django_tables2 as tables
from crispy_forms.layout import Row
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from project.views import BreadcrumbMixin

from crud_views.lib.breadcrumb import Breadcrumb, BreadcrumbItem
from crud_views.lib.crispy import Column6, Column12, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem
from crud_views.lib.table import LinkChildColumn, LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import AncestorPolicy, ParentViewSet, ViewSet
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired, GuardianListViewPermissionRequired
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_object_detail.lib import ObjectDetailMixin, ObjectDetailViewPermissionRequired
from navbar_demo.models import Address, Customer, Item, Order, Tenant

cv_tenant = GuardianViewSet(
    model=Tenant,
    name="navbar_tenant",
    icon_header="fa-solid fa-building",
    ancestor_policy=AncestorPolicy(provider="guardian", accept_global_perms=False),
)


class TenantTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    customers = LinkChildColumn(name="navbar_customer", verbose_name=_("Customers"))


class TenantListView(BreadcrumbMixin, ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_tenant
    table_class = TenantTable


class TenantDetailView(BreadcrumbMixin, ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_tenant
    cv_property_display = [{"title": _("Tenant"), "properties": ["id", "name"]}]


class NavbarDemoHomeView(BreadcrumbMixin, LoginRequiredMixin, TemplateView):
    template_name = "navbar_demo/home.html"

    def cv_breadcrumb_get(self):
        return Breadcrumb(items=(*self.cv_breadcrumb_prefix(), BreadcrumbItem(title=_("Object navigation"))))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cv_breadcrumb"] = self.cv_breadcrumb()
        tenants = cv_tenant.get_objects_for_user(self.request.user, "view")
        context["customers"] = (
            Customer.objects.filter(tenant__in=tenants).select_related("tenant")
            if self.request.user.has_perm("navbar_demo.view_customer")
            else Customer.objects.none()
        )
        return context


cv_customer = ViewSet(
    model=Customer,
    name="navbar_customer",
    parent=ParentViewSet(name="navbar_tenant", attribute="tenant"),
    ancestor_policy=AncestorPolicy(cascade=True),
    icon_header="fa-solid fa-address-card",
)

customer_navbar = NavBar(
    viewset="navbar_customer",
    items=[
        NavItem(key="detail", label=_("Details")),
        NavItem(key="notes", label=_("Notes")),
        NavItem(child="navbar_order", label=_("Orders")),
        NavItem(child="navbar_address", label=_("Addresses")),
    ],
)


class NavbarMixin(CrudViewNavBarMixin):
    cv_navbar = customer_navbar


class CustomerForm(CrispyModelForm):
    class Meta:
        model = Customer
        fields = ["name", "notes"]  # Tenant comes from the authorized URL, never from form data.

    def get_layout_fields(self):
        return [Row(Column6("name")), Row(Column12("notes"))]


class CustomerTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class CustomerListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_customer
    table_class = CustomerTable


class CustomerDetailView(NavbarMixin, BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_customer
    cv_property_display = [{"title": _("Customer"), "properties": ["id", "name", "tenant"]}]


class CustomerNotesView(NavbarMixin, BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_customer
    cv_key = "notes"
    cv_path = "notes"
    cv_action_short_label_template_code = _("Notes")
    cv_property_display = [{"title": _("Notes"), "properties": ["notes"]}]


class CustomerCreateView(BreadcrumbMixin, CrispyViewMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_customer
    form_class = CustomerForm


class CustomerUpdateView(NavbarMixin, BreadcrumbMixin, CrispyViewMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_customer
    form_class = CustomerForm


class CustomerDeleteView(NavbarMixin, BreadcrumbMixin, CrispyViewMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_customer
    form_class = CrispyDeleteForm


cv_order = ViewSet(
    model=Order,
    name="navbar_order",
    parent=ParentViewSet(name="navbar_customer", attribute="customer"),
    ancestor_policy=AncestorPolicy(cascade=True),
    icon_header="fa-solid fa-cart-shopping",
)


class OrderForm(CrispyModelForm):
    class Meta:
        model = Order
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column6("name"))


class OrderTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    items = LinkChildColumn(name="navbar_item", verbose_name=_("Items"))


class OrderListView(NavbarMixin, BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_order
    table_class = OrderTable


class OrderDetailView(NavbarMixin, BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_order
    cv_property_display = [{"title": _("Order"), "properties": ["id", "name", "customer"]}]


class OrderCreateView(
    NavbarMixin, BreadcrumbMixin, CrispyViewMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_order
    form_class = OrderForm


class OrderUpdateView(NavbarMixin, BreadcrumbMixin, CrispyViewMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_order
    form_class = OrderForm


class OrderDeleteView(BreadcrumbMixin, CrispyViewMixin, DeleteViewPermissionRequired):
    # An intermediate view can omit the bar without affecting Item navigation.
    cv_viewset = cv_order
    form_class = CrispyDeleteForm


cv_item = ViewSet(
    model=Item,
    name="navbar_item",
    parent=ParentViewSet(name="navbar_order", attribute="order"),
    ancestor_policy=AncestorPolicy(cascade=True),
    icon_header="fa-solid fa-box",
)


class ItemForm(CrispyModelForm):
    class Meta:
        model = Item
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column6("name"))


class ItemTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class ItemListView(NavbarMixin, BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_item
    table_class = ItemTable


class ItemDetailView(NavbarMixin, BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_item
    cv_property_display = [{"title": _("Item"), "properties": ["id", "name", "order"]}]


class ItemCreateView(
    NavbarMixin, BreadcrumbMixin, CrispyViewMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_item
    form_class = ItemForm


class ItemUpdateView(NavbarMixin, BreadcrumbMixin, CrispyViewMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_item
    form_class = ItemForm


class ItemDeleteView(NavbarMixin, BreadcrumbMixin, CrispyViewMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_item
    form_class = CrispyDeleteForm


cv_address = ViewSet(
    model=Address,
    name="navbar_address",
    parent=ParentViewSet(name="navbar_customer", attribute="customer"),
    ancestor_policy=AncestorPolicy(cascade=True),
    icon_header="fa-solid fa-location-dot",
)


class AddressForm(CrispyModelForm):
    class Meta:
        model = Address
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column6("name"))


class AddressTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class AddressListView(NavbarMixin, BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_address
    table_class = AddressTable


class AddressDetailView(NavbarMixin, BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_address
    cv_property_display = [{"title": _("Address"), "properties": ["id", "name", "customer"]}]


class AddressCreateView(
    NavbarMixin, BreadcrumbMixin, CrispyViewMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_address
    form_class = AddressForm


class AddressUpdateView(NavbarMixin, BreadcrumbMixin, CrispyViewMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_address
    form_class = AddressForm


class AddressDeleteView(NavbarMixin, BreadcrumbMixin, CrispyViewMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_address
    form_class = CrispyDeleteForm
