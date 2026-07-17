from django.db import models
from django_fsm import FSMField, transition

from crud_views_workflow.lib.enums import BadgeEnum, WorkflowComment
from crud_views_workflow.lib.mixins import WorkflowModelMixin


class CampaignState(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    ERROR = "error", "Error"


class Campaign(WorkflowModelMixin, models.Model):
    STATE_CHOICES = CampaignState
    STATE_BADGES = {
        CampaignState.DRAFT: BadgeEnum.LIGHT,
        CampaignState.ACTIVE: BadgeEnum.INFO,
        CampaignState.COMPLETED: BadgeEnum.PRIMARY,
        CampaignState.CANCELLED: BadgeEnum.WARNING,
        CampaignState.ERROR: BadgeEnum.DANGER,
    }

    name = models.CharField(max_length=128)
    state = FSMField(default=CampaignState.DRAFT, choices=CampaignState.choices)

    def __str__(self):
        return self.name

    @transition(
        field=state,
        source=CampaignState.DRAFT,
        target=CampaignState.ACTIVE,
        on_error=CampaignState.ERROR,
        custom={"label": "Activate", "comment": WorkflowComment.NONE},
    )
    def wf_activate(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.ACTIVE,
        target=CampaignState.COMPLETED,
        on_error=CampaignState.ERROR,
        custom={"label": "Complete", "comment": WorkflowComment.OPTIONAL},
    )
    def wf_complete(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=[CampaignState.DRAFT, CampaignState.ACTIVE],
        target=CampaignState.CANCELLED,
        on_error=CampaignState.ERROR,
        custom={"label": "Cancel", "comment": WorkflowComment.REQUIRED},
    )
    def wf_cancel(self, request=None, by=None, comment=None):
        pass
