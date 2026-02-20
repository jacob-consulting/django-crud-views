import django_tables2 as tables
from crispy_forms.layout import Row
from django.utils.translation import gettext_lazy as _

from django_object_detail import PropertyConfig

from app.models.campaign import Campaign
from crud_views.lib.crispy import CrispyModelForm, Column4, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.table import Table, LinkDetailColumn
from crud_views.lib.views import DetailViewPermissionRequired, UpdateViewPermissionRequired, \
    CreateViewPermissionRequired, \
    ListViewTableMixin, DeleteViewPermissionRequired, ListViewPermissionRequired, MessageMixin
from crud_views.lib.viewset import ViewSet
from crud_views_workflow.forms import WorkflowForm
from crud_views_workflow.views import WorkflowView

cv_campaign = ViewSet(
    model=Campaign,
    name="campaign",
    icon_header="fa-solid fa-bullhorn"
)


class CampaignForm(CrispyModelForm):
    submit_label = "Create"

    class Meta:
        model = Campaign
        fields = ["name"]

    def get_layout_fields(self):
        return Row(Column4("name"))


class CampaignUpdateForm(CampaignForm):
    submit_label = "Update"


class CampaignTable(Table):
    id = LinkDetailColumn()
    name = tables.Column(attrs=Table.ca.w70)
    state = tables.Column(accessor="state_badge", attrs=Table.ca.w20)


class CampaignListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_campaign
    cv_list_actions = ["detail", "workflow", "update", "delete"]
    table_class = CampaignTable


class CampaignDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_campaign

    property_display = [
        {
            "title": "Properties",
            "icon": "megaphone",
            "description": "Campaign attributes",
            "properties": [
                "id",
                "name",
                PropertyConfig(path="state_badge", title=_("State"), detail="Campaign workflow state"),
            ],
        },
    ]


class CampaignUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = CampaignUpdateForm
    cv_viewset = cv_campaign


class CampaignCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    form_class = CampaignForm
    cv_viewset = cv_campaign


class CampaignDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_campaign


class CampaignWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = Campaign


class CampaignWorkflowView(CrispyModelViewMixin, MessageMixin, WorkflowView):
    cv_context_actions = ["list", "detail", "workflow"]
    cv_viewset = cv_campaign
    form_class = CampaignWorkflowForm
