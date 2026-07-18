import django_tables2 as tables
from crispy_forms.layout import Row

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
    submit_label = "Save"

    class Meta:
        model = Company
        fields = ["name", "city"]

    def get_layout_fields(self):
        return Row(Column6("name"), Column6("city"))


class CompanyTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    city = tables.Column()
    departments = LinkChildColumn(name="department", verbose_name="Departments", attrs=Table.ca.w10)
    offices = LinkChildColumn(name="office", verbose_name="Offices", attrs=Table.ca.w10)


class CompanyListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_company
    table_class = CompanyTable


class CompanyDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_company
    cv_property_display = [
        {"title": "Company", "icon": "building", "properties": ["id", "name", "city"]},
    ]


class CompanyCreateView(CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_company
    form_class = CompanyForm
    cv_message = "Created company »{object}«"


class CompanyUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_company
    form_class = CompanyForm
    cv_message = "Updated company »{object}«"


class CompanyDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_company
    form_class = CrispyDeleteForm
    cv_message = "Deleted company »{object}«"


# --------------------------------------------------------------------------- Department (child of Company)

cv_department = ViewSet(
    model=Department,
    name="department",
    parent=ParentViewSet(name="company"),
    icon_header="fa-solid fa-people-group",
)


class DepartmentForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Department
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column6("name"))


class DepartmentTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    employees = LinkChildColumn(name="employee", verbose_name="Employees", attrs=Table.ca.w10)


class DepartmentListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_department
    table_class = DepartmentTable


class DepartmentDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_department
    cv_property_display = [
        {"title": "Department", "icon": "people-group", "properties": ["id", "name", "company"]},
    ]


class DepartmentCreateView(CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_department
    form_class = DepartmentForm
    cv_message = "Created department »{object}«"


class DepartmentUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_department
    form_class = DepartmentForm
    cv_message = "Updated department »{object}«"


class DepartmentDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_department
    form_class = CrispyDeleteForm
    cv_message = "Deleted department »{object}«"


# --------------------------------------------------------------------------- Employee (grandchild)

cv_employee = ViewSet(
    model=Employee,
    name="employee",
    parent=ParentViewSet(name="department"),
    icon_header="fa-regular fa-id-badge",
)


class EmployeeForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Employee
        fields = ["name", "email"]

    def get_layout_fields(self):
        return Row(Column6("name"), Column6("email"))


class EmployeeTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    email = tables.Column()


class EmployeeListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_employee
    table_class = EmployeeTable


class EmployeeDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_employee
    cv_property_display = [
        {"title": "Employee", "icon": "id-badge", "properties": ["id", "name", "email", "department"]},
    ]


class EmployeeCreateView(CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_employee
    form_class = EmployeeForm
    cv_message = "Created employee »{object}«"


class EmployeeUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_employee
    form_class = EmployeeForm
    cv_message = "Updated employee »{object}«"


class EmployeeDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_employee
    form_class = CrispyDeleteForm
    cv_message = "Deleted employee »{object}«"


# --------------------------------------------------------------------------- Office (second child of Company)

cv_office = ViewSet(
    model=Office,
    name="office",
    parent=ParentViewSet(name="company"),
    icon_header="fa-solid fa-door-open",
)


class OfficeForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Office
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column6("name"))


class OfficeTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class OfficeListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_office
    table_class = OfficeTable


class OfficeDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_office
    cv_property_display = [
        {"title": "Office", "icon": "door-open", "properties": ["id", "name", "company"]},
    ]


class OfficeCreateView(CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_office
    form_class = OfficeForm
    cv_message = "Created office »{object}«"


class OfficeUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_office
    form_class = OfficeForm
    cv_message = "Updated office »{object}«"


class OfficeDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_office
    form_class = CrispyDeleteForm
    cv_message = "Deleted office »{object}«"
