"""Native submit controls for one workflow ChoiceField."""

from django.forms.widgets import ChoiceWidget


class _TransitionButtons(ChoiceWidget):
    template_name = "crud_views_workflow/widgets/transitions.html"
    use_fieldset = False

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)
        self.actions = []
        self.label = ""

    def id_for_label(self, id_, index=None):
        # A click on the visible field label must never submit a transition.
        return ""

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        attrs = widget["attrs"]
        attrs["class"] = " ".join(
            token for token in attrs.get("class", "").split() if token not in {"form-control", "form-select"}
        )
        attrs.pop("required", None)
        widget["label"] = self.label
        widget["actions"] = self.actions
        return context
