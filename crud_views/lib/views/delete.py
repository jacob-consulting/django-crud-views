from crud_views.lib.views.mixins import CrudViewProcessFormMixin
from django.utils.translation import gettext_lazy as _
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class DeleteView(CrudViewProcessFormMixin, CrudView, generic.DeleteView):
    template_name = "crud_views/view_delete.html"

    cv_key = "delete"
    cv_path = "delete"
    cv_success_key = "list"
    cv_context_actions = crud_views_settings.delete_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/delete.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/delete.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/delete.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/delete.html"

    # icons
    cv_icon_action = "fa-regular fa-trash-can"

    # messages
    cv_message_template: str | None = "crud_views/snippets/message/delete.html"

    def cv_form_valid(self, context: dict):
        """
        Handle valid form, delete the object
        """
        self.object.delete()


class DeleteViewPermissionRequired(CrudViewPermissionRequiredMixin, DeleteView):  # this file
    cv_permission = "delete"
