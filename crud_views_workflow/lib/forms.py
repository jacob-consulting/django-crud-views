from typing import List

from crispy_forms.layout import Row
from django.forms import RadioSelect, ChoiceField, CharField
from django.forms.widgets import Textarea
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import CrispyForm, Column8
from .enums import WorkflowComment


class WorkflowForm(CrispyForm):
    """
    Workflow form
    """

    class Meta:
        fields = ["transition", "comment"]

    submit_label: str = _('Process Workflow Step')

    transition = ChoiceField(
        choices=tuple(),
        widget=RadioSelect,
        label="LABEL-PLACEHOLDER",
        help_text="HELP-PLACEHOLDER",
        required=True,
    )
    comment = CharField(
        label="LABEL-PLACEHOLDER",
        help_text="HELP-PLACEHOLDER",
        required=False,  # will be set dynamically
        widget=Textarea(attrs={
            "rows": 4,
            "placeholder": _("Add your comment…"),
        }),
    )

    def get_layout_fields(self):
        return Row(Column8("transition")), Row(Column8("comment"))

    def __init__(self, *args, choices: List[tuple[str, str]], transition_comments: dict, **kwargs):
        super().__init__(*args, **kwargs)
        self.transition_comments = transition_comments
        self.transition_comment = max(
            transition_comments.values()) if transition_comments.values() else WorkflowComment.NONE

        # hide the comment field if not required
        if self.transition_comment == WorkflowComment.NONE:
            field_comment = self.fields['comment']
            field_comment.widget = field_comment.hidden_widget()

        transition = self.fields["transition"]
        transition.choices = choices
        transition.widget.use_fieldset = False

    def clean(self):
        cleaned_data = super().clean()
        transition = cleaned_data.get("transition")
        comment = cleaned_data.get("comment")
        if isinstance(comment, str):
            comment = comment.strip()
        transition_comment = self.transition_comments.get(transition)
        if transition_comment == WorkflowComment.REQUIRED and not comment:
            self.add_error("comment", _("Comment is required for this transition"))
