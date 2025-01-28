import django_tables2 as tables

from app.models import Baz
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet, ParentViewSet

vs_baz = ViewSet(
    model=Baz,
    name="baz",
    parent=ParentViewSet(name="bar")
)


class BazTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()


class BazListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Baz
    table_class = BazTable
    vs = vs_baz
    vs_list_actions = ["detail", "update", "delete"]


class BazDetailView(DetailViewPermissionRequired):
    model = Baz
    vs = vs_baz
    vs_properties = ["id", "name"]


class BazUpdateView(UpdateViewPermissionRequired):
    model = Baz
    fields = ["name"]
    vs = vs_baz


class BazCreateView(CreateViewPermissionRequired):
    model = Baz
    fields = ["name"]
    vs = vs_baz


class BazDeleteView(DeleteViewPermissionRequired):
    model = Baz
    vs = vs_baz
