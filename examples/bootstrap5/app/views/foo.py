import django_tables2 as tables
from crispy_forms.layout import Row
from crud_views.lib.views.detail import PropertyGroup

from app.models import Foo
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkChildColumn, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet

cv_foo = ViewSet(
    model=Foo,
    name="foo",
    icon_header="fa-solid fa-paw"
)


class FooForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Foo
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class FooTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    bar = LinkChildColumn(name="bar", verbose_name="Bar", empty_values=())



class FooListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Foo
    table_class = FooTable
    cv_viewset = cv_foo
    cv_list_actions = ["detail", "update", "delete"]


class FooDetailView(DetailViewPermissionRequired):
    model = Foo
    cv_viewset = cv_foo

    cv_properties = ["id", "name"]

    cv_property_groups = [
        PropertyGroup(
            key="properties",
            label="Properties",
            properties=[
                "id",
                "name",
            ]
        ),
    ]


class FooUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Foo
    form_class = FooForm
    cv_viewset = cv_foo


class FooCreateView(CrispyModelViewMixin, CreateViewPermissionRequired):
    model = Foo
    form_class = FooForm
    cv_viewset = cv_foo


class FooDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Foo
    form_class = CrispyDeleteForm
    cv_viewset = cv_foo
