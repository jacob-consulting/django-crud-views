from collections.abc import Iterable
from contextlib import nullcontext
from functools import partial

from django.core.exceptions import ImproperlyConfigured
from django.db import connections, router, transaction
from django.utils.translation import gettext_lazy as _

from crud_views.lib.check import Check, CheckAttribute, CheckExpression
from crud_views.lib.view import CrudViewPermissionRequiredMixin
from crud_views.lib.views.form import CustomFormView

from .execution import _run_transition, _WorkflowRefusal
from .mixins import WorkflowModelMixin

_PROCESS_WORKFLOW = _("Process workflow")


class WorkflowView(CustomFormView):
    """
    Base view for workflow transitions using the WorkflowForm
    """

    form_class = None
    cv_key = "workflow"
    cv_path = "workflow"

    template_name = "crud_views_workflow/view_workflow.html"

    cv_icon_header = "workflow"
    cv_icon_action = "workflow"
    cv_message_template_code = _("Successfully processed workflow step on “{{ object }}”")
    cv_header_template_code = _PROCESS_WORKFLOW
    cv_paragraph_template_code = _("Process workflow step on “{{ object }}”")
    cv_action_label_template_code = _PROCESS_WORKFLOW
    cv_action_short_label_template_code = _PROCESS_WORKFLOW

    cv_transition_label = _("Select a possible workflow action to take")
    cv_transition_help_text = None
    cv_comment_label = _("Please provide a comment for your workflow step")
    cv_comment_help_text = None
    cv_transition_presentation = "radio"

    @classmethod
    def checks(cls) -> Iterable[Check]:
        yield from super().checks()
        # form_class must be set to a WorkflowForm subclass
        yield CheckAttribute(context=cls, id="E230", attribute="form_class")
        # workflow-specific label attributes must not be None
        yield CheckAttribute(context=cls, id="E231", attribute="cv_transition_label")
        yield CheckAttribute(context=cls, id="E232", attribute="cv_comment_label")
        # the model associated with this view must extend WorkflowModelMixin
        if cls.cv_viewset is not None:
            model = cls.cv_viewset.model
            yield CheckExpression(
                context=cls,
                id="E233",
                expression=issubclass(model, WorkflowModelMixin),
                msg=f"Model »{model.__name__}» must extend WorkflowModelMixin",
            )
            # required WorkflowModelMixin class attributes must be set on the model
            if issubclass(model, WorkflowModelMixin):
                yield CheckAttribute(context=model, id="E234", attribute="STATE_CHOICES")
                yield CheckAttribute(context=model, id="E235", attribute="STATE_BADGES")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # apply custom labels and help texts
        form.fields["transition"].label = self.cv_transition_label
        form.fields["transition"].help_text = self.cv_transition_help_text
        form.fields["comment"].label = self.cv_comment_label
        form.fields["comment"].help_text = self.cv_comment_help_text
        form._workflow_configure()
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.object.workflow_get_form_kwargs(self.request.user))
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_workflow_choices"] = self.object.workflow_has_any_possible_transition(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        self.cv_post_hook(context)
        if self.cv_form_is_valid(context):
            try:
                self.cv_form_valid_process(context)
            except _WorkflowRefusal as refusal:
                # Both write boundaries have unwound. Fetch through the scoped
                # queryset rather than refreshing a possibly protected FSM instance.
                form = context["form"]
                form.add_error(refusal.field, refusal)
                self.object = self.get_object(queryset=self.get_queryset().using(self._cv_get_workflow_db_alias()))
                form._workflow_refresh()
                context = self.get_context_data(object=self.object, form=form, **kwargs)
            else:
                return self.cv_form_valid_redirect(context)
        self.cv_form_invalid_hook(context)
        return self.cv_form_invalid(context)

    def cv_get_db_alias(self) -> str:
        return router.db_for_write(type(self.object), instance=self.object)

    def _cv_get_workflow_db_alias(self):
        """Select once after scoped object resolution; all write boundaries reuse it."""
        if not hasattr(self, "_cv_workflow_db_alias"):
            using = self.cv_get_db_alias()
            if not isinstance(using, str) or not using or using not in connections:
                raise ImproperlyConfigured("cv_get_db_alias() must select a configured database alias")
            self._cv_workflow_db_alias = using
        return self._cv_workflow_db_alias

    def cv_get_atomic(self):
        using = self._cv_get_workflow_db_alias()
        return transaction.atomic(using=using) if self.cv_atomic else nullcontext()

    def cv_form_valid_process(self, context: dict) -> None:
        using = self._cv_get_workflow_db_alias()
        with self.cv_get_atomic():
            self.cv_form_valid(context)
            self.cv_form_valid_hook(context)
            transaction.on_commit(partial(self.cv_on_commit, context), using=using)

    def cv_form_valid(self, context: dict):
        form = context["form"]

        def on_transition(info):
            context["workflow_info"] = info
            self.on_transition(
                info, info.transition, info.state_old, info.state_new, info.comment, self.request.user, info.data
            )

        _run_transition(
            self.object,
            form.cleaned_data["transition"],
            user=self.request.user,
            comment=form.cleaned_data["comment"],
            using=self._cv_get_workflow_db_alias(),
            on_transition=on_transition,
        )

    def on_transition(self, info, transition, state_old, state_new, comment, user, data):
        """
        Override for database follow-ups of a transition. Runs inside the transaction, so
        writes here roll back together with the transition. Put side effects (mail, Celery,
        webhooks) in cv_on_commit instead; context["workflow_info"] holds the record there.
        """
        pass


class WorkflowViewPermissionRequired(CrudViewPermissionRequiredMixin, WorkflowView):
    cv_permission = "change"
