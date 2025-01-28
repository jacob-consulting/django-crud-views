from django.utils.translation import gettext_lazy as _

from crud_views.lib.view import ViewSetViewPermissionRequiredMixin
from .action import ActionView
from ..settings import crud_views_settings


class OrderedCheckBase:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ordered_model.models import OrderedModel
        if not issubclass(self.model, OrderedModel):
            raise ValueError(f"{self.model} is not a subclass of OrderedModel")


class OrderedUpView(OrderedCheckBase, ActionView):
    vs_key = "up"
    vs_path = "up"
    vs_backend_only = True

    # texts and labels
    vs_action_label_template: str = crud_views_settings.up_action_label_template
    vs_action_label_template_code: str = crud_views_settings.up_action_label_template_code
    vs_action_short_label_template: str = crud_views_settings.up_action_short_label_template
    vs_action_short_label_template_code: str = crud_views_settings.up_action_short_label_template_code

    vs_message_template: str | None = crud_views_settings.up_action_message_template
    vs_message_template_code: str | None = crud_views_settings.up_action_message_template_code

    vs_icon_action = "fa-regular fa-circle-up"

    def action(self, context: dict) -> bool:
        self.object.up()
        self.object.save()
        return True


class OrderedUpViewPermissionRequired(ViewSetViewPermissionRequiredMixin, OrderedUpView):  # this file
    vs_permission = "change"


class OrderedDownView(OrderedCheckBase, ActionView):
    vs_key = "down"
    vs_path = "down"
    vs_backend_only = True

    # texts and labels
    vs_action_label_template: str = crud_views_settings.down_action_label_template
    vs_action_label_template_code: str = crud_views_settings.down_action_label_template_code
    vs_action_short_label_template: str = crud_views_settings.down_action_short_label_template
    vs_action_short_label_template_code: str = crud_views_settings.down_action_short_label_template_code

    vs_message_template: str | None = crud_views_settings.down_action_message_template
    vs_message_template_code: str | None = crud_views_settings.down_action_message_template_code

    vs_icon_action = "fa-regular fa-circle-down"

    def action(self, context: dict) -> bool:
        self.object.down()
        self.object.save()
        return True


class OrderedUpDownPermissionRequired(ViewSetViewPermissionRequiredMixin, OrderedDownView):  # this file
    vs_permission = "change"
