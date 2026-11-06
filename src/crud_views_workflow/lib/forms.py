from crispy_forms.layout import Row
from django.forms import CharField, ChoiceField, RadioSelect
from django.forms.widgets import Textarea
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import Column8, CrispyForm

from .enums import WorkflowComment
from .execution import _check_transition_business, _check_transition_comment, _WorkflowRefusal


class WorkflowForm(CrispyForm):
    """
    Workflow form
    """

    class Meta:
        # RUF012: Django Meta option, not a typed class attribute
        fields = ["transition", "comment"]  # noqa: RUF012

    submit_label: str = _("Process Workflow Step")
    # the workflow icon replaces the submit kind's save icon; a subclass submit_icon wins
    submit_icon: str | None = "workflow"

    transition = ChoiceField(
        choices=(),
        widget=RadioSelect,
        label="LABEL-PLACEHOLDER",
        help_text="HELP-PLACEHOLDER",
        required=True,
    )
    comment = CharField(
        label="LABEL-PLACEHOLDER",
        help_text="HELP-PLACEHOLDER",
        required=False,  # will be set dynamically
        widget=Textarea(
            attrs={
                "rows": 4,
                "placeholder": _("Add your comment…"),
            }
        ),
    )

    def get_layout_fields(self):
        return Row(Column8("transition")), Row(Column8("comment"))

    def __init__(self, *args, choices: list[tuple[str, str]], transition_comments: dict, **kwargs):
        super().__init__(*args, **kwargs)
        self._workflow_comment_widget = self.fields["comment"].widget
        self._workflow_set_choices(choices, transition_comments)
        self.fields["transition"].widget.use_fieldset = False

    def _workflow_set_choices(self, choices, transition_comments):
        self.transition_comments = transition_comments
        self.transition_comment = (
            max(transition_comments.values()) if transition_comments.values() else WorkflowComment.NONE
        )

        # hide the comment field if not required
        if self.transition_comment == WorkflowComment.NONE:
            field_comment = self.fields["comment"]
            field_comment.widget = field_comment.hidden_widget()
        elif self.fields["comment"].widget.is_hidden:
            self.fields["comment"].widget = self._workflow_comment_widget

        self.fields["transition"].choices = choices

    def _workflow_refresh(self):
        """Refresh object-derived choices without replacing the bound form or data."""
        kwargs = self.cv_view.object.workflow_get_form_kwargs(self.cv_view.request.user)
        self._workflow_set_choices(kwargs["choices"], kwargs["transition_comments"])

    def clean(self):
        cleaned_data = super().clean()
        transition = cleaned_data.get("transition")
        comment = cleaned_data.get("comment")
        transition_comment = self.transition_comments.get(transition)
        # add_error removes the field from cleaned_data, so retain both inputs
        # before independently checking business blockers and comment requiredness.
        if transition and self.cv_view is not None:
            try:
                _check_transition_business(self.cv_view.object, transition, user=self.cv_view.request.user)
            except _WorkflowRefusal as refusal:
                self.add_error(refusal.field, refusal)
        try:
            _check_transition_comment(transition_comment, comment)
        except _WorkflowRefusal as refusal:
            self.add_error(refusal.field, refusal)
        return cleaned_data
