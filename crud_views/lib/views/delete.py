from django.utils.translation import gettext_lazy as _
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import ViewSetView, ViewSetViewPermissionRequiredMixin


class DeleteView(ViewSetView, generic.DeleteView):
    template_name = "crud_views/view_delete.html"

    vs_key = "delete"
    vs_path = "delete"
    vs_success_key = "list"
    vs_context_actions = crud_views_settings.delete_context_actions

    # texts and labels
    vs_header_template: str = crud_views_settings.delete_header_template
    vs_header_template_code: str = crud_views_settings.delete_header_template_code
    vs_paragraph_template: str = crud_views_settings.delete_paragraph_template
    vs_paragraph_template_code: str = crud_views_settings.delete_paragraph_template_code
    vs_action_label_template: str = crud_views_settings.delete_action_label_template
    vs_action_label_template_code: str = crud_views_settings.delete_action_label_template_code
    vs_action_short_label_template: str = crud_views_settings.delete_action_short_label_template
    vs_action_short_label_template_code: str = crud_views_settings.delete_action_short_label_template_code

    vs_message_template: str | None = crud_views_settings.delete_message_template
    vs_message_template_code: str | None = crud_views_settings.delete_message_template_code

    vs_icon_action = "fa-regular fa-trash-can"


class DeleteViewPermissionRequired(ViewSetViewPermissionRequiredMixin, DeleteView):  # this file
    vs_permission = "delete"
