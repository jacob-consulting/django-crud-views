import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from context_buttons.models import Ticket
from crud_views.lib.crispy import Column4, Column8, Column12, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.view import ContextButton
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet, context_buttons_default

cv_ticket = ViewSet(
    model=Ticket,
    name="ticket",
    icon_header="fa-solid fa-ticket",
    context_buttons=[
        *context_buttons_default(),
        # whole-button template, inline: a big solid edit button instead of the default icon button
        ContextButton(
            key="edit_big",
            key_target="update",
            template_code=(
                '<a href="{{ cv_url }}" class="btn btn-primary btn-lg cv-demo-edit-big" cv-key="{{ cv_key }}">'
                '<i class="{{ cv_icon_action }}" aria-hidden="true"></i> {{ cv_action_label }}</a>'
            ),
        ),
        # whole-button template, from a file: a pill-shaped edit button (templates/context_buttons/)
        ContextButton(key="edit_pill", key_target="update", template="context_buttons/pill_button.html"),
    ],
)


class TicketForm(CrispyModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "priority", "description"]

    def get_layout_fields(self):
        return [Row(Column8("title"), Column4("priority")), Row(Column12("description"))]


class TicketTable(Table):
    id = LinkDetailColumn()
    title = tables.Column()
    priority = tables.Column()


class TicketListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_ticket
    table_class = TicketTable
    cv_list_actions = ["detail", "update", "delete"]


class TicketDetailView(BreadcrumbMixin, DetailViewPermissionRequired):
    cv_viewset = cv_ticket
    # the header toolbar: edit_big is drawn by its own template_code; like every context button it is
    # hidden for a user who may not change the ticket (log in as bob)
    cv_context_actions = ["home", "edit_big", "delete"]
    # places the buttons by hand with cv_context_button / cv_context_url / cv_context_has_permission
    # and a custom loop over cv_get_context_buttons
    template_name = "context_buttons/ticket_detail.html"


class TicketCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_ticket
    form_class = TicketForm
    cv_message_template_code = _("Created ticket “{{ object }}”")


class TicketUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_ticket
    form_class = TicketForm
    cv_message_template_code = _("Updated ticket “{{ object }}”")
    cv_cancel_keys = ["list", "detail"]


class TicketDeleteView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_ticket
    form_class = CrispyDeleteForm
    cv_message_template_code = _("Deleted ticket “{{ object }}”")
    cv_cancel_keys = ["list", "detail"]
