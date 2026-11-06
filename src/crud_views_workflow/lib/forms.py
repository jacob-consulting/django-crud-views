from uuid import uuid4

from crispy_forms.layout import Row
from django.core.exceptions import ImproperlyConfigured
from django.forms import CharField, ChoiceField, RadioSelect
from django.forms.widgets import Textarea
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from crud_views.lib.crispy import Column8, CrispyForm
from crud_views.lib.crispy.actions import _ThemedFormActions

from .enums import WorkflowComment
from .execution import _check_transition_business, _check_transition_comment, _WorkflowRefusal
from .widgets import _TransitionButtons


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
        # Keep wrapping local to the stock opt-in layout, including field labels/help.
        attrs = {"style": "overflow-wrap: anywhere;"} if self._workflow_presentation == "buttons" else {}
        comment = "comment" if self.fields["comment"].widget.is_hidden else Row(Column8("comment", **attrs))
        return Row(Column8("transition", **attrs)), comment

    def __init__(self, *args, choices: list[tuple[str, str]], transition_comments: dict, **kwargs):
        super().__init__(*args, **kwargs)
        self._workflow_presentation = getattr(self.cv_view, "cv_transition_presentation", "radio")
        if self._workflow_presentation not in ("radio", "buttons"):
            raise ImproperlyConfigured("cv_transition_presentation must be 'radio' or 'buttons'")
        if self._workflow_presentation == "buttons":
            self._workflow_id = f"cv-wf-{uuid4().hex}"
            self.auto_id = f"{self._workflow_id}-%s"
            self.fields["transition"].widget = _TransitionButtons(attrs=self.fields["transition"].widget.attrs)
        self._workflow_comment_widget = self.fields["comment"].widget
        self._workflow_set_choices(choices, transition_comments)
        self.fields["transition"].widget.use_fieldset = False

    def get_form_actions(self):
        if self._workflow_presentation == "buttons":
            self._workflow_prepare_descriptions()
            cancel = self.get_cancel_button()
            return _ThemedFormActions(*([cancel] if cancel is not None else []))
        return super().get_form_actions()

    def get_cancel_button_kwargs(self):
        kwargs = super().get_cancel_button_kwargs()
        if self._workflow_presentation == "buttons":
            kwargs["css_id"] = f"{self._workflow_id}-cancel"
        return kwargs

    def _workflow_prepare_descriptions(self):
        """Reference crispy's stable error paragraphs on every supported Django."""
        for name, field in self.fields.items():
            bound = self[name]
            attrs = field.widget.attrs
            # Preserve application descriptions; replace only our generated IDs.
            tokens = [
                token
                for token in attrs.get("aria-describedby", "").split()
                if token not in {f"{bound.auto_id}_helptext", f"{bound.auto_id}_error"}
                and not (token.startswith("error_") and token.endswith(f"_{bound.auto_id}"))
            ]
            if not field.widget.is_hidden:
                if field.help_text:
                    tokens.append(f"{bound.auto_id}_helptext")
                tokens.extend(f"error_{index + 1}_{bound.auto_id}" for index in range(len(bound.errors)))
            if tokens:
                attrs["aria-describedby"] = " ".join(dict.fromkeys(tokens))
            else:
                attrs.pop("aria-describedby", None)

    def _workflow_configure(self):
        """Configure after subclass construction and view labels, once per refresh."""
        for name in ("transition", "comment"):
            raw = getattr(self.cv_view, f"cv_{name}_help_text", None)
            self.fields[name].help_text = escape(raw) if raw else raw
            if self._workflow_presentation == "buttons":
                self.fields[name].label = escape(getattr(self.cv_view, f"cv_{name}_label"))
        self._bound_fields_cache.clear()
        if self._workflow_presentation != "buttons":
            return
        field = self.fields["transition"]
        widget = field.widget
        widget.label = field.label
        widget.help_text = getattr(self.cv_view, "cv_transition_help_text", None)
        field.help_text = ""
        steps = {step.name: step for step in self.cv_view.object.get_all_state_transitions()}
        actions = []
        for index, (name, label) in enumerate(field.choices):
            blockers = []
            try:
                _check_transition_business(self.cv_view.object, name, user=self.cv_view.request.user)
            except _WorkflowRefusal as refusal:
                blockers = refusal.messages
            actions.append(
                {
                    "name": name,
                    "label": label,
                    "blockers": blockers,
                    "id": f"{self['transition'].auto_id}-action-{index}",
                    "help_text": steps[name].custom.get("help_text"),
                    "comment_required": self.transition_comments.get(name) == WorkflowComment.REQUIRED,
                }
            )
        widget.actions = actions

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
        self._workflow_configure()

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
