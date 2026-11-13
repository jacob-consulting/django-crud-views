import django_tables2 as tables
from crispy_forms.layout import Row
from django import forms
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from project.views import BreadcrumbMixin

from crud_views.lib.conditional import ConditionalGroup, ConditionalGroupModelForm, ToggleGroup
from crud_views.lib.crispy import Column8, CrispyViewMixin
from crud_views.lib.table import Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet
from queryset_conditional.conditions import REMOTE_CONDITION, VISIT_CONDITION
from queryset_conditional.models import Service, ServiceRequest

cv_service_request = ViewSet(
    model=ServiceRequest, name="service_request", prefix="service-request", icon_header="fa-solid fa-toolbox"
)


class RequestForm(ConditionalGroupModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.annotate(conditional_category=F("category__code")), label=_("Service")
    )
    cv_conditional_groups = [
        ConditionalGroup(toggle=VISIT_CONDITION, fields=["visit_address"], required=["visit_address"]),
        ConditionalGroup(toggle=REMOTE_CONDITION, fields=["meeting_url"], required=["meeting_url"]),
    ]

    class Meta:
        model = ServiceRequest
        fields = ["service", "visit_address", "meeting_url"]

    def get_layout_fields(self):
        return [
            Row(Column8("service")),
            ToggleGroup(VISIT_CONDITION, Row(Column8("visit_address")), legend=_("On-site visit")),
            ToggleGroup(REMOTE_CONDITION, Row(Column8("meeting_url")), legend=_("Remote meeting")),
        ]


class RequestTable(Table):
    service = tables.Column()
    visit_address = tables.Column()
    meeting_url = tables.Column()


class RequestListView(BreadcrumbMixin, ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_service_request
    table_class = RequestTable

    def get_queryset(self):
        return super().get_queryset().select_related("service")


class RequestCreateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_service_request
    form_class = RequestForm
    cv_message_template_code = _("Created service request “{{ object }}”")


class RequestUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_service_request
    form_class = RequestForm
    cv_message_template_code = _("Updated service request “{{ object }}”")
