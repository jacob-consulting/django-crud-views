from django.db import models
from django.utils.translation import gettext as _
from django_fsm import FSMField, transition

from crud_views_workflow.lib.enums import WorkflowComment
from crud_views_workflow.lib.enums import BadgeEnum
from crud_views_workflow.lib.mixins import WorkflowModelMixin


class CampaignState(models.TextChoices):
    NEW = "new", _("New")
    ACTIVE = "active", _("Active")
    SUCCESS = "success", _("Success")
    CANCELED = "canceled", _("Cancelled")
    ERROR = "error", _("Error")


class Campaign(WorkflowModelMixin, models.Model):
    STATE_CHOICES = CampaignState
    STATE_BADGES = {
        CampaignState.NEW: BadgeEnum.LIGHT,
        CampaignState.ACTIVE: BadgeEnum.INFO,
        CampaignState.SUCCESS: BadgeEnum.PRIMARY,
        CampaignState.CANCELED: BadgeEnum.WARNING,
        CampaignState.ERROR: BadgeEnum.DANGER,
    }

    TRANSITION_COMMENT_OPTIONAL = 1
    TRANSITION_COMMENT_REQUIRED = 2

    name = models.CharField(max_length=128)
    state = FSMField(default=CampaignState.NEW, choices=CampaignState.choices)

    def __str__(self):
        return self.name

    @transition(
        field=state,
        source=CampaignState.NEW,
        target=CampaignState.ACTIVE,
        on_error=CampaignState.ERROR,
        custom={"label": _("Activate"), "comment": WorkflowComment.NONE},
    )
    def wf_activate(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.ACTIVE,
        target=CampaignState.SUCCESS,
        on_error=CampaignState.ERROR,
        custom={"label": _("Done"), "comment": WorkflowComment.OPTIONAL},
    )
    def wf_done(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.NEW,
        target=CampaignState.CANCELED,
        on_error=CampaignState.ERROR,
        custom={"label": _("Cancel"), "comment": WorkflowComment.REQUIRED},
    )
    def wf_cancel_new(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.ACTIVE,
        target=CampaignState.CANCELED,
        on_error=CampaignState.ERROR,
        custom={"label": _("Cancel"), "comment": WorkflowComment.REQUIRED},
    )
    def wf_cancel_active(self, request=None, by=None, comment=None):
        pass
