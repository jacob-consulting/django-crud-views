from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from crud_views_workflow.lib import BadgeEnum, WorkflowComment, WorkflowModelMixin


class CampaignState(models.TextChoices):
    DRAFT = "draft", _("Draft")
    ACTIVE = "active", _("Active")
    COMPLETED = "completed", _("Completed")
    CANCELLED = "cancelled", _("Cancelled")
    ERROR = "error", _("Error")


class Campaign(WorkflowModelMixin, models.Model):
    STATE_CHOICES = CampaignState
    STATE_BADGES = {
        CampaignState.DRAFT: BadgeEnum.LIGHT,
        CampaignState.ACTIVE: BadgeEnum.INFO,
        CampaignState.COMPLETED: BadgeEnum.PRIMARY,
        CampaignState.CANCELLED: BadgeEnum.WARNING,
        CampaignState.ERROR: BadgeEnum.DANGER,
    }

    name = models.CharField(_("name"), max_length=128)
    state = FSMField(_("state"), default=CampaignState.DRAFT, choices=CampaignState.choices)

    class Meta:
        verbose_name = _("campaign")
        verbose_name_plural = _("campaigns")

    def __str__(self):
        return self.name

    @transition(
        field=state,
        source=CampaignState.DRAFT,
        target=CampaignState.ACTIVE,
        on_error=CampaignState.ERROR,
        custom={"label": _("Activate"), "comment": WorkflowComment.NONE},
    )
    def wf_activate(self, request=None, by=None, comment=None):
        # The state change is all there is: django-fsm sets the field, WorkflowModelMixin logs it.
        pass

    @transition(
        field=state,
        source=CampaignState.ACTIVE,
        target=CampaignState.COMPLETED,
        on_error=CampaignState.ERROR,
        custom={"label": _("Complete"), "comment": WorkflowComment.OPTIONAL},
    )
    def wf_complete(self, request=None, by=None, comment=None):
        # The state change is all there is: django-fsm sets the field, WorkflowModelMixin logs it.
        pass

    @transition(
        field=state,
        source=[CampaignState.DRAFT, CampaignState.ACTIVE],
        target=CampaignState.CANCELLED,
        on_error=CampaignState.ERROR,
        custom={"label": _("Cancel"), "comment": WorkflowComment.REQUIRED},
    )
    def wf_cancel(self, request=None, by=None, comment=None):
        # The state change is all there is: django-fsm sets the field, WorkflowModelMixin logs it.
        pass
