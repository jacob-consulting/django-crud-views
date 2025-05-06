from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin
from .mixins import CrudViewProcessFormMixin


class UpdateView(CrudViewProcessFormMixin, CrudView, generic.UpdateView):
    template_name = "crud_views/view_update.html"

    cv_key = "update"
    cv_path = "update"
    cv_success_key = "list"
    cv_context_actions = crud_views_settings.update_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/update.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/update.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/update.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/update.html"

    # icons
    cv_icon_action = "fa-regular fa-pen-to-square"

    # messages
    cv_message_template: str | None = "crud_views/snippets/message/update.html"

    def cv_form_valid(self, context: dict):
        """
        Handle valid form, save (update) the from instance
        """
        self.object = context["form"].save()


class UpdateViewPermissionRequired(CrudViewPermissionRequiredMixin, UpdateView):  # this file
    cv_permission = "change"
