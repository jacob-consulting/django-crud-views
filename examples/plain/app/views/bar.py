import django_tables2 as tables

from app.models import Bar
from crud_views.lib.table import Table, LinkChildColumn, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, CreateViewPermissionRequired, \
    ListViewPermissionRequired, ListViewTableMixin, DeleteViewPermissionRequired
from crud_views.lib.viewset import ViewSet, ParentViewSet

vs_bar = ViewSet(
    model=Bar,
    name="bar",
    parent=ParentViewSet(name="foo")
)


class BarTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    baz = LinkChildColumn(name="baz", verbose_name="Baz", empty_values=())


class BarListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Bar
    table_class = BarTable
    vs = vs_bar
    vs_list_actions = ["detail", "update", "delete"]


class BarDetailView(DetailViewPermissionRequired):
    model = Bar
    vs = vs_bar
    vs_properties = ["id", "name"]


class BarUpdateView(UpdateViewPermissionRequired):
    model = Bar
    fields = ["name"]
    vs = vs_bar


class BarCreateView(CreateViewPermissionRequired):
    model = Bar
    fields = ["name"]
    vs = vs_bar


class BarDeleteView(DeleteViewPermissionRequired):
    model = Bar
    vs = vs_bar
