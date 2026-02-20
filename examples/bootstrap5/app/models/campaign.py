from django.db import models
from django.utils.translation import gettext as _
from django_fsm import FSMField, transition

from crud_views_workflow.mixins import WorkflowMixin


class CampaignState(models.TextChoices):
    NEW = "new", _("New")
    ACTIVE = "active", _("Active")
    SUCCESS = "success", _("Success")
    CANCELED = "canceled", _("Cancelled")
    ERROR = "error", _("Error")


class Campaign(WorkflowMixin, models.Model):
    STATE_ENUM = CampaignState
    STATE_BADGES = {
        CampaignState.NEW: "light",
        CampaignState.ACTIVE: "info",
        CampaignState.SUCCESS: "primary",
        CampaignState.CANCELED: "warning",
        CampaignState.ERROR: "danger",
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
        custom={"label": _("Activate"), "comment": WorkflowMixin.Comment.NONE},
    )
    def wf_activate(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.ACTIVE,
        target=CampaignState.SUCCESS,
        on_error=CampaignState.ERROR,
        custom={"label": _("Done"), "comment": WorkflowMixin.Comment.OPTIONAL},
    )
    def wf_done(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.NEW,
        target=CampaignState.CANCELED,
        on_error=CampaignState.ERROR,
        custom={"label": _("Cancel"), "comment": WorkflowMixin.Comment.REQUIRED},
    )
    def wf_cancel_new(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=CampaignState.ACTIVE,
        target=CampaignState.CANCELED,
        on_error=CampaignState.ERROR,
        custom={"label": _("Cancel"), "comment": WorkflowMixin.Comment.REQUIRED},
    )
    def wf_cancel_active(self, request=None, by=None, comment=None):
        pass
