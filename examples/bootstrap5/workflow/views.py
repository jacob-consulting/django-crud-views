import django_tables2 as tables
from crispy_forms.layout import Row

from crud_views.lib.crispy import Column6, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import LinkDetailColumn, Table
from crud_views.lib.views import (
    CreateViewPermissionRequired,
    DeleteViewPermissionRequired,
    DetailViewPermissionRequired,
    ListViewPermissionRequired,
    ListViewTableMixin,
    MessageMixin,
    UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet
from crud_views_workflow.lib import WorkflowForm, WorkflowViewPermissionRequired

from workflow.models import Campaign

cv_campaign = ViewSet(model=Campaign, name="campaign", icon_header="fa-solid fa-bullhorn")


class CampaignForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Campaign
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column6("name"))


class CampaignTable(Table):
    id = LinkDetailColumn()
    name = tables.Column(attrs=Table.ca.w70)
    state = tables.Column(accessor="state_badge", attrs=Table.ca.w20)


class CampaignListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_campaign
    table_class = CampaignTable
    cv_list_actions = ["detail", "workflow", "update", "delete"]


class CampaignDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_campaign
    cv_context_actions = ["home", "detail", "update", "workflow", "delete"]
    cv_property_display = [
        {
            "title": "Campaign",
            "icon": "bullhorn",
            "properties": [
                "id",
                "name",
                {"path": "state_badge", "title": "State", "detail": "Current workflow state"},
            ],
        },
    ]


class CampaignCreateView(CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_campaign
    form_class = CampaignForm
    cv_message = "Created campaign »{object}«"


class CampaignUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_campaign
    cv_context_actions = ["home", "detail", "update", "workflow", "delete"]
    form_class = CampaignForm
    cv_message = "Updated campaign »{object}«"


class CampaignDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_campaign
    cv_context_actions = ["home", "detail", "update", "workflow", "delete"]
    form_class = CrispyDeleteForm
    cv_message = "Deleted campaign »{object}«"


class CampaignWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = Campaign


class CampaignWorkflowView(CrispyViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_viewset = cv_campaign
    cv_context_actions = ["list", "detail", "update", "workflow"]
    form_class = CampaignWorkflowForm
