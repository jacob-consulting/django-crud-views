import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.crispy import Column6, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    ActionViewPermissionRequired,
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from disabled_actions.models import Ticket

# "ticket" is taken by the Context Buttons example; ViewSet names are global
cv_lockable_ticket = ViewSet(model=Ticket, name="lockable_ticket", icon_header="fa-solid fa-lock")


class TicketForm(CrispyModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "locked"]

    def get_layout_fields(self):
        return Row(Column6("title"), Column6("locked"))


class TicketTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    locked = tables.BooleanColumn()


class TicketListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_lockable_ticket
    table_class = TicketTable
    cv_list_actions = ["detail", "update", "lock", "delete"]
    cv_context_actions = ["create"]


class TicketDetailView(BreadcrumbMixin, ObjectDetailViewPermissionRequired):
    cv_viewset = cv_lockable_ticket
    cv_context_actions = ["list", "update", "lock", "delete"]
    cv_property_display = [
        {"title": _("Ticket"), "icon": "fas:lock", "properties": ["title", "locked"]},
    ]


class TicketCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_lockable_ticket
    form_class = TicketForm
    cv_message_template_code = _("Created ticket “{{ object }}”")


def ticket_is_open(obj):
    """The state gate shared by update and delete: a locked ticket can be neither edited nor deleted."""
    return not (obj and obj.locked)


class TicketUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_lockable_ticket
    form_class = TicketForm
    cv_inaccessible_actions = "disable"  # a locked ticket shows update greyed out ...
    cv_message_template_code = _("Updated ticket “{{ object }}”")

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        return ticket_is_open(obj)


class TicketDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_lockable_ticket
    form_class = CrispyDeleteForm
    # cv_inaccessible_actions left at the default "hide": ... and delete not at all
    cv_message_template_code = _("Deleted ticket “{{ object }}”")

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        return ticket_is_open(obj)


class TicketLockView(BreadcrumbMixin, MessageMixin, ActionViewPermissionRequired):
    """Always enabled, so a locked ticket can be unlocked again."""

    cv_viewset = cv_lockable_ticket
    cv_key = "lock"
    cv_path = "lock"
    cv_permission = "change"
    cv_backend_only = True
    cv_icon_action = "fa-solid fa-lock"
    cv_action_label_template_code = _("Lock / unlock")
    cv_action_short_label_template_code = _("Lock / unlock")
    cv_message_template_code = _("Toggled lock for “{{ object }}”")
    cv_message_template_error_code = _("Could not toggle lock for “{{ object }}”")

    def action(self, context) -> bool:
        self.object.locked = not self.object.locked
        self.object.save(update_fields=["locked"])
        return True
