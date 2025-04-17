import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext as _

from app.models import Group
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    CreateViewPermissionRequired,
    MessageMixin,
    ListViewTableMixin,
    ListViewPermissionRequired,
    DeleteViewPermissionRequired, RedirectChildView
)
from crud_views.lib.views.detail import PropertyGroup
from crud_views.lib.viewset import ViewSet

cv_group = ViewSet(
    model=Group,
    name="group",
    icon_header="fa-solid fa-user-group"
)


class GroupCreateForm(CrispyModelForm):
    submit_label = _("Create")

    class Meta:
        model = Group
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class GroupUpdateForm(GroupCreateForm):
    """
    Update form has the same fields as the create form
    """
    submit_label = _("Update")


class GroupTable(Table):
    id = LinkDetailColumn(attrs=Table.ca.ID)
    name = tables.Column()


class GroupListView(ListViewTableMixin, ListViewPermissionRequired):
    model = Group

    cv_viewset = cv_group
    cv_list_actions = ["detail", "update", "delete",
                       "redirect_child"
                       ]

    table_class = GroupTable


class GroupCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    model = Group
    form_class = GroupCreateForm
    cv_viewset = cv_group
    cv_message = "Created author »{object}«"


class GroupUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    model = Group
    form_class = GroupUpdateForm
    cv_viewset = cv_group
    cv_message = "Updated author »{object}«"


class GroupDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    model = Group
    form_class = CrispyDeleteForm
    cv_viewset = cv_group
    cv_message = "Deleted author »{object}«"


class GroupDetailView(DetailViewPermissionRequired):
    model = Group
    cv_viewset = cv_group
    # cv_context_actions = ["home", "update", "contact", "delete"]

    cv_property_groups = [
        PropertyGroup(
            key="attributes",
            label=_("Attributes"),
            properties=[
                "id",
                "name",
            ]
        ),
    ]


class RedirectMembersView(RedirectChildView):
    cv_action_label = _("Manage Members")
    cv_redirect = "members"
    cv_redirect_key = "list"
    cv_icon_action = "fa-regular fa-user"

    cv_viewset = cv_group
