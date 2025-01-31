from django.utils.translation import gettext_lazy as _
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin


class DeleteView(CrudView, generic.DeleteView):
    template_name = "crud_views/view_delete.html"

    cv_key = "delete"
    cv_path = "delete"
    cv_success_key = "list"
    cv_context_actions = crud_views_settings.delete_context_actions

    # texts and labels
    cv_header_template: str = crud_views_settings.delete_header_template
    cv_header_template_code: str = crud_views_settings.delete_header_template_code
    cv_paragraph_template: str = crud_views_settings.delete_paragraph_template
    cv_paragraph_template_code: str = crud_views_settings.delete_paragraph_template_code
    cv_action_label_template: str = crud_views_settings.delete_action_label_template
    cv_action_label_template_code: str = crud_views_settings.delete_action_label_template_code
    cv_action_short_label_template: str = crud_views_settings.delete_action_short_label_template
    cv_action_short_label_template_code: str = crud_views_settings.delete_action_short_label_template_code

    cv_message_template: str | None = crud_views_settings.delete_message_template
    cv_message_template_code: str | None = crud_views_settings.delete_message_template_code

    cv_icon_action = "fa-regular fa-trash-can"


class DeleteViewPermissionRequired(CrudViewPermissionRequiredMixin, DeleteView):  # this file
    cv_permission = "delete"
