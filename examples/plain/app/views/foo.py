import django_tables2 as tables

from app.models import Foo
from crud_views.lib.table import Table, LinkChildColumn, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet

cv_foo = ViewSet(
    model=Foo,
    name="foo",
)

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


class FooUpdateView(UpdateViewPermissionRequired):
    model = Foo
    fields = ["name"]
    cv_viewset = cv_foo


class FooCreateView(CreateViewPermissionRequired):
    model = Foo
    fields = ["name"]
    cv_viewset = cv_foo


class FooDeleteView(DeleteViewPermissionRequired):
    model = Foo
    cv_viewset = cv_foo
