from django.utils.translation import gettext_lazy as _

from crud_views.lib.view import CrudViewPermissionRequiredMixin
from .action import ActionView
from ..settings import crud_views_settings


class OrderedCheckBase:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ordered_model.models import OrderedModel
        # todo: move to system checks
        if not issubclass(self.model, OrderedModel):
            raise ValueError(f"{self.model} is not a subclass of OrderedModel")


class OrderedUpView(ActionView):
    cv_key = "up"
    cv_path = "up"
    cv_backend_only = True

    # texts and labels
    cv_action_label_template: str | None = "crud_views/snippets/action/up.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/up.html"

    # icons
    cv_icon_action = "fa-regular fa-circle-up"

    # messages
    cv_message_template: str | None = "crud_views/snippets/message/up.html"

    def action(self, context: dict) -> bool:
        return self.up(context)

    def up(self, context: dict) -> bool:
        self.object.up()
        self.object.save()
        return True


class OrderedUpViewPermissionRequired(CrudViewPermissionRequiredMixin, OrderedUpView):  # this file
    cv_permission = "change"


class OrderedDownView(ActionView):
    cv_key = "down"
    cv_path = "down"
    cv_backend_only = True

    # texts and labels
    cv_action_label_template: str | None = "crud_views/snippets/action/down.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/down.html"

    # icons
    cv_icon_action = "fa-regular fa-circle-down"

    # messages
    cv_message_template: str | None = "crud_views/snippets/message/down.html"

    def action(self, context: dict) -> bool:
        return self.down(context)

    def down(self, context: dict) -> bool:
        self.object.up()
        self.object.save()
        return True


class OrderedUpDownPermissionRequired(CrudViewPermissionRequiredMixin, OrderedDownView):  # this file
    cv_permission = "change"
