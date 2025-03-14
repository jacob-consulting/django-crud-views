import django_tables2 as tables
from crispy_forms.layout import Row

from app.models import Foo
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkChildColumn, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from .menu import MenuMixin


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



class FooListView(MenuMixin,ListViewTableMixin, ListViewPermissionRequired):
    model = Foo
    table_class = FooTable
    cv_viewset = cv_foo
    cv_list_actions = ["detail", "update", "delete"]


class FooDetailView(MenuMixin, DetailViewPermissionRequired):
    model = Foo
    cv_viewset = cv_foo
    cv_properties = ["id", "name"]


class FooUpdateView(MenuMixin,CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Foo
    form_class = FooForm
    cv_viewset = cv_foo


class FooCreateView(MenuMixin, CrispyModelViewMixin, CreateViewPermissionRequired):
    model = Foo
    form_class = FooForm
    cv_viewset = cv_foo


class FooDeleteView(MenuMixin, CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Foo
    form_class = CrispyDeleteForm
    cv_viewset = cv_foo
