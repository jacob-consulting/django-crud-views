import django_tables2 as tables
from crispy_forms.layout import Row
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView
from project.views import BreadcrumbMixin

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
from navbar_demo.models import Customer, Tenant

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


class NavbarDemoHomeView(LoginRequiredMixin, RedirectView):
    pattern_name = "navbar_tenant-list"
    permanent = False


cv_customer = ViewSet(
    model=Customer,
    name="navbar_customer",
    parent=ParentViewSet(name="navbar_tenant", attribute="tenant"),
    icon_header="fa-solid fa-address-card",
)

customer_navbar = NavBar(
    viewset="navbar_customer",
    items=[NavItem(key="detail", label=_("Details")), NavItem(key="notes", label=_("Notes"))],
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
