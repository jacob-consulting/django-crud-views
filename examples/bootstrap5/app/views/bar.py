import django_tables2 as tables
from crispy_forms.layout import Row

from app.models import Bar
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkChildColumn, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet, ParentViewSet
from .menu import MenuMixin

cv_bar = ViewSet(
    model=Bar,
    name="bar",
    parent=ParentViewSet(name="foo"),
    icon_header="fa-solid fa-bone"
)


class BarForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Bar
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class BarTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()
    baz = LinkChildColumn(name="baz", verbose_name="Baz", empty_values=())


class BarListView(MenuMixin, ListViewTableMixin, ListViewPermissionRequired):
    model = Bar
    table_class = BarTable
    cv_viewset = cv_bar
    cv_list_actions = ["detail", "update", "delete"]


class BarDetailView(MenuMixin, DetailViewPermissionRequired):
    model = Bar
    cv_viewset = cv_bar
    cv_properties = ["id", "name"]


class BarUpdateView(MenuMixin, CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Bar
    form_class = BarForm

    cv_viewset = cv_bar


class BarCreateView(MenuMixin, CrispyModelViewMixin, CreateViewPermissionRequired):
    model = Bar
    form_class = BarForm
    cv_viewset = cv_bar


class BarDeleteView(MenuMixin, CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Bar
    form_class = CrispyDeleteForm
    cv_viewset = cv_bar
