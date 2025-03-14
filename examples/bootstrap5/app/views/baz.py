import django_tables2 as tables
from crispy_forms.layout import Row

from app.models import Baz
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, \
    CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired
from crud_views.lib.viewset import ViewSet, ParentViewSet
from .menu import MenuMixin

cv_baz = ViewSet(
    model=Baz,
    name="baz",
    parent=ParentViewSet(name="bar"),
    icon_header="fa-solid fa-dog"
)


class BazForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Baz
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class BazTable(Table):
    id = LinkDetailColumn()
    name = tables.Column()

    def render_baz(self, record):
        return "baz"


class BazListView(MenuMixin, ListViewTableMixin, ListViewPermissionRequired):
    model = Baz
    table_class = BazTable
    cv_viewset = cv_baz
    cv_list_actions = ["detail", "update", "delete"]


class BazDetailView(MenuMixin, DetailViewPermissionRequired):
    model = Baz
    cv_viewset = cv_baz
    cv_properties = ["id", "name"]


class BazUpdateView(MenuMixin, CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Baz
    form_class = BazForm

    cv_viewset = cv_baz


class BazCreateView(MenuMixin, CrispyModelViewMixin, CreateViewPermissionRequired):
    model = Baz
    form_class = BazForm
    cv_viewset = cv_baz


class BazDeleteView(MenuMixin, CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Baz
    form_class = CrispyDeleteForm
    cv_viewset = cv_baz
