"""Native submit controls for one workflow ChoiceField."""

from django.forms.widgets import ChoiceWidget

from crud_views.lib.button_classes import get_button_class


class _TransitionButtons(ChoiceWidget):
    template_name = "crud_views_workflow/widgets/transitions.html"
    use_fieldset = False

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)
        self.actions = []
        self.label = ""
        self.help_text = None

    def id_for_label(self, id_, index=None):
        # A click on the visible field label must never submit a transition.
        return ""

    def get_context(self, name, value, attrs):
        # The view package requires initialized apps; WorkflowForm also supports pre-setup imports.
        from crud_views.lib.view.button_data import icon_host_keys

        # Transition variants are a fixed contract, independent of extensible state badge colours.
        variants = ("primary", "secondary", "success", "danger", "warning", "info", "light", "dark")
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        attrs = widget["attrs"]
        attrs["class"] = " ".join(
            token for token in attrs.get("class", "").split() if token not in {"form-control", "form-select"}
        )
        attrs.pop("required", None)
        widget["label"] = self.label
        widget["help_text"] = self.help_text
        widget["help_id"] = f"{attrs['id']}-help"
        tokens = attrs.get("aria-describedby", "").split()
        if self.help_text:
            tokens.append(widget["help_id"])
        if tokens:
            attrs["aria-describedby"] = " ".join(dict.fromkeys(tokens))
        widget["actions"] = []
        widget["comment_required"] = any(action["comment_required"] for action in self.actions)
        for action in self.actions:
            action = dict(action)
            variant = action.get("variant")
            action["button_class"] = (
                get_button_class("workflow", "transition-" + variant)
                if isinstance(variant, str) and variant in variants
                else get_button_class("form", "submit", "label")
            )
            action["icon_class"], action["icon_inline"] = icon_host_keys(action.get("icon"), "form")
            descriptions = list(tokens)
            action["help_id"] = f"{action['id']}-help"
            action["blockers_id"] = f"{action['id']}-blockers"
            if action["help_text"]:
                descriptions.append(action["help_id"])
            if action["blockers"]:
                descriptions.append(action["blockers_id"])
            action["describedby"] = " ".join(dict.fromkeys(descriptions))
            widget["actions"].append(action)
        return context
