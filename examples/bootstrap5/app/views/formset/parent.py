import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext as _

from app.models.poly import Parent
from crud_views.lib.crispy import CrispyModelViewMixin, CrispyDeleteForm, CrispyModelForm, Column4
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.views import (
    ListViewTableMixin,
    ListViewPermissionRequired,
    RedirectChildView, CreateViewPermissionRequired, UpdateViewPermissionRequired, DeleteViewPermissionRequired
)
from crud_views.lib.viewset import ViewSet

cv_poly_parent_formset = ViewSet(
    model=Parent,
    name="parent",
    pk=ViewSet.PK.UUID,
    icon_header="fa-solid fa-user-group"
)


class ParentForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Parent
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class ParentTable(Table):
    id = UUIDLinkDetailColumn(attrs=Table.ca.ID)
    name = tables.Column(attrs=Table.ca.w80)


class ParentListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Parent

    cv_viewset = cv_poly_parent_formset
    cv_list_actions = ["redirect_child", "update", "delete"]

    table_class = ParentTable


class ParentCreateView(CrispyModelViewMixin, CreateViewPermissionRequired):
    model = Parent
    form_class = ParentForm
    cv_viewset = cv_poly_parent_formset


class ParentUpdateView(CrispyModelViewMixin, UpdateViewPermissionRequired):
    model = Parent
    form_class = ParentForm
    cv_viewset = cv_poly_parent_formset


class ParentDeleteView(CrispyModelViewMixin, DeleteViewPermissionRequired):
    model = Parent
    form_class = CrispyDeleteForm
    cv_viewset = cv_poly_parent_formset


class RedirectPolyView(RedirectChildView):
    cv_action_label = _("Manage Poly")
    cv_redirect = "poly"
    cv_redirect_key = "list"
    cv_icon_action = "fa-solid fa-sun"

    cv_viewset = cv_poly_parent_formset
