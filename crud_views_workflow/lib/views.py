from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views.form import CustomFormView
from ..models import WorkflowInfo


class WorkflowView(CustomFormView):
    """
    Base view for workflow transitions using the WorkflowForm
    """

    STATE_BADGES_DEFAULT = "info"

    form_class = None
    cv_key = "workflow"
    cv_path = "workflow"

    template_name = "crud_views_workflow/view_workflow.html"

    cv_icon_header = "fa-solid fa-diagram-project"
    cv_icon_action = "fa-solid fa-diagram-project"
    cv_message_template_code = _("Successfully processed workflow step on »{{ object }}«")
    cv_header_template_code = _("Process workflow")
    cv_paragraph_template_code = _("Process workflow step")
    cv_action_label_template_code = _("Process workflow")
    cv_action_short_label_template_code = _("Process workflow")

    cv_transition_label = _("Select a possible workflow action to take")
    cv_transition_help_text = None
    cv_comment_label = _("Please provide a comment for your workflow step")
    cv_comment_help_text = None

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # apply custom labels and help texts
        form.fields["transition"].label = self.cv_transition_label
        form.fields["transition"].help_text = self.cv_transition_help_text
        form.fields["comment"].label = self.cv_comment_label
        form.fields["comment"].help_text = self.cv_comment_help_text

        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.object.workflow_get_form_kwargs(self.request.user))
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_workflow_choices"] = self.object.workflow_has_any_possible_transition(self.request.user)
        return context

    # todo: cv_form_valid instead of cv_form_valid_hook?
    def cv_form_valid_hook(self, context: dict):
        """
        Process workflow transition
        """
        form = context["form"]
        transition = form.cleaned_data["transition"]
        comment = form.cleaned_data["comment"]
        if isinstance(comment, str):
            comment = comment.strip()
        if not comment:
            comment = None

        # some security: make sure the user is allowed to take this transition
        if not self.object.workflow_has_transition(self.request.user, transition):
            raise SuspiciousOperation(f"Invalid transition {transition}")

        # get method to call
        wf_method = getattr(self.object, transition, None)
        assert callable(wf_method), f"Invalid transition {transition}"

        # todo: configurable
        with transaction.atomic():

            # get old state
            state_old = self.object.state

            # execute the workflow
            data = wf_method(by=self.request.user, comment=comment)

            # save object
            self.object.save()

            # new state
            state_new = self.object.state
            user = self.request.user

            # and save the workflow state
            info = WorkflowInfo.objects.create(
                transition=transition,
                state_old=state_old,
                state_new=state_new,
                comment=comment,
                user=user,
                data=data,
                workflow_object_id=self.object.id,
                workflow_object_content_type=ContentType.objects.get_for_model(self.object),
            )

            # call hook
            self.on_transition(info, transition, state_old, state_new, comment, user, data)

    def on_transition(self, info, transition, state_old, state_new, comment, user, data):
        """
        Override this to do additional stuff after a transition
        """
        pass


class WorkflowViewPermissionRequired(CrudViewPermissionRequiredMixin, WorkflowView):
    cv_permission = "change"
   