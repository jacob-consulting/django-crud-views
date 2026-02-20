from django.db import models
from django.utils.translation import gettext as _
from django_fsm import FSMField, transition

from crud_views_workflow.mixins import WorkflowMixin


class Campaign(WorkflowMixin, models.Model):
    class STATE:
        NEW = "new"
        ACTIVE = "active"
        SUCCESS = "success"
        CANCELED = "canceled"
        ERROR = "error"

    STATE_CHOICES = (
        (STATE.NEW, _("New")),
        (STATE.ACTIVE, _("Active")),
        (STATE.SUCCESS, _("Success")),
        (STATE.CANCELED, _("Cancelled")),
        (STATE.ERROR, _("Error")),
    )

    STATE_BADGES = {
        STATE.NEW: "light",
        STATE.ACTIVE: "info",
        STATE.SUCCESS: "primary",
        STATE.CANCELED: "warning",
        STATE.ERROR: "danger",
    }

    TRANSITION_COMMENT_OPTIONAL = 1
    TRANSITION_COMMENT_REQUIRED = 2

    name = models.CharField(max_length=128)
    state = FSMField(default=STATE.NEW, choices=STATE_CHOICES)

    def __str__(self):
        return self.name

    @transition(
        field=state,
        source=STATE.NEW,
        target=STATE.ACTIVE,
        on_error=STATE.ERROR,
        custom={"label": _("Activate"), "comment": WorkflowMixin.Comment.NONE},
    )
    def wf_activate(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=STATE.ACTIVE,
        target=STATE.SUCCESS,
        on_error=STATE.ERROR,
        custom={"label": _("Done"), "comment": WorkflowMixin.Comment.OPTIONAL},
    )
    def wf_done(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=STATE.NEW,
        target=STATE.CANCELED,
        on_error=STATE.ERROR,
        custom={"label": _("Cancel"), "comment": WorkflowMixin.Comment.REQUIRED},
    )
    def wf_cancel_new(self, request=None, by=None, comment=None):
        pass

    @transition(
        field=state,
        source=STATE.ACTIVE,
        target=STATE.CANCELED,
        on_error=STATE.ERROR,
        custom={"label": _("Cancel"), "comment": WorkflowMixin.Comment.REQUIRED},
    )
    def wf_cancel_active(self, request=None, by=None, comment=None):
        pass
