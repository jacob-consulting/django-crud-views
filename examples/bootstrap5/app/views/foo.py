import django_tables2 as tables
from crispy_forms.layout import Row

from app.models import Foo
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkChildColumn, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet

vs_foo = ViewSet(
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
    vs = vs_foo
    vs_list_actions = ["detail", "update", "delete"]


class FooDetailView(DetailViewPermissionRequired):
    model = Foo
    vs = vs_foo
    vs_properties = ["id", "name"]


class FooUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Foo
    form_class = FooForm
    vs = vs_foo


class FooCreateView(CrispyModelViewMixin, CreateViewPermissionRequired):
    model = Foo
    form_class = FooForm
    vs = vs_foo


class FooDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Foo
    form_class = CrispyDeleteForm
    vs = vs_foo
