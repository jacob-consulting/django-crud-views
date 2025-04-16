import django_tables2 as tables
from crispy_forms.layout import Row
from crud_views.lib.views.detail import PropertyGroup

from app.models import Baz
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, \
    CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired, CreateViewParentMixin
from crud_views.lib.viewset import ViewSet, ParentViewSet

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


class BazListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Baz
    table_class = BazTable
    cv_viewset = cv_baz
    cv_list_actions = ["detail", "update", "delete"]


class BazDetailView(DetailViewPermissionRequired):
    model = Baz
    cv_viewset = cv_baz
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


class BazUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Baz
    form_class = BazForm

    cv_viewset = cv_baz


class BazCreateView(CrispyModelViewMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    model = Baz
    form_class = BazForm
    cv_viewset = cv_baz


class BazDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Baz
    form_class = CrispyDeleteForm
    cv_viewset = cv_baz
