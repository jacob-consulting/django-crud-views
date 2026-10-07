import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.crispy import Column6, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkChildColumn, LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewParentMixin,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ParentViewSet, ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from nested.models import Company, Department, Employee, Office

# --------------------------------------------------------------------------- Company (root)

cv_company = ViewSet(model=Company, name="company", icon_header="fa-solid fa-building")


class CompanyForm(CrispyModelForm):
    class Meta:
        model = Company
        fields = ["name", "city"]

    def get_layout_fields(self):
        return Row(Column6("name"), Column6("city"))


class CompanyTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    city = tables.Column()
    departments = LinkChildColumn(name="department", verbose_name=_("Departments"), attrs=Table.ca.w10)
    offices = LinkChildColumn(name="office", verbose_name=_("Offices"), attrs=Table.ca.w10)


class CompanyListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_company
    table_class = CompanyTable


class CompanyDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_company
    cv_property_display = [
        {"title": _("Company"), "icon": "building", "properties": ["id", "name", "city"]},
    ]


class CompanyCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_company
    form_class = CompanyForm
    cv_message_template_code = _("Created company “{{ object }}”")


class CompanyUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_company
    form_class = CompanyForm
    cv_message_template_code = _("Updated company “{{ object }}”")


class CompanyDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_company
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted company “{{ object }}”")


# --------------------------------------------------------------------------- Department (child of Company)

cv_department = ViewSet(
    model=Department,
    name="department",
    parent=ParentViewSet(name="company"),
    icon_header="fa-solid fa-people-group",
)


class DepartmentForm(CrispyModelForm):
    class Meta:
        model = Department
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column6("name"))


class DepartmentTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    employees = LinkChildColumn(name="employee", verbose_name=_("Employees"), attrs=Table.ca.w10)


class DepartmentListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_department
    table_class = DepartmentTable


class DepartmentDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_department
    cv_property_display = [
        {"title": _("Department"), "icon": "people-group", "properties": ["id", "name", "company"]},
    ]


class DepartmentCreateView(
    BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_department
    form_class = DepartmentForm
    cv_message_template_code = _("Created department “{{ object }}”")


class DepartmentUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_department
    form_class = DepartmentForm
    cv_message_template_code = _("Updated department “{{ object }}”")


class DepartmentDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_department
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted department “{{ object }}”")


# --------------------------------------------------------------------------- Employee (grandchild)

cv_employee = ViewSet(
    model=Employee,
    name="employee",
    parent=ParentViewSet(name="department"),
    icon_header="fa-regular fa-id-badge",
)


class EmployeeForm(CrispyModelForm):
    class Meta:
        model = Employee
        fields = ["name", "email"]

    def get_layout_fields(self):
        return Row(Column6("name"), Column6("email"))


class EmployeeTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    email = tables.Column()


class EmployeeListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_employee
    table_class = EmployeeTable


class EmployeeDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_employee
    cv_property_display = [
        {"title": _("Employee"), "icon": "id-badge", "properties": ["id", "name", "email", "department"]},
    ]


class EmployeeCreateView(
    BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_employee
    form_class = EmployeeForm
    cv_message_template_code = _("Created employee “{{ object }}”")


class EmployeeUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_employee
    form_class = EmployeeForm
    cv_message_template_code = _("Updated employee “{{ object }}”")


class EmployeeDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_employee
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted employee “{{ object }}”")


# --------------------------------------------------------------------------- Office (second child of Company)

cv_office = ViewSet(
    model=Office,
    name="office",
    parent=ParentViewSet(name="company"),
    icon_header="fa-solid fa-door-open",
)


class OfficeForm(CrispyModelForm):
    class Meta:
        model = Office
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column6("name"))


class OfficeTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class OfficeListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_office
    table_class = OfficeTable


class OfficeDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_office
    cv_property_display = [
        {"title": _("Office"), "icon": "door-open", "properties": ["id", "name", "company"]},
    ]


class OfficeCreateView(
    BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired
):
    cv_viewset = cv_office
    form_class = OfficeForm
    cv_message_template_code = _("Created office “{{ object }}”")


class OfficeUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_office
    form_class = OfficeForm
    cv_message_template_code = _("Updated office “{{ object }}”")


class OfficeDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_office
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted office “{{ object }}”")
