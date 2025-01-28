from django.utils.translation import gettext_lazy as _
from django.views import generic

from crud_views.lib.view import ViewSetView, ViewSetViewPermissionRequiredMixin
from crud_views.lib.settings import crud_views_settings


class UpdateView(ViewSetView, generic.UpdateView):
    template_name = "crud_views/view.update.html"

    vs_key = "update"
    vs_path = "update"
    vs_success_key = "list"
    vs_context_actions = crud_views_settings.update_context_actions

    # texts and labels
    vs_header_template: str = crud_views_settings.update_header_template
    vs_header_template_code: str = crud_views_settings.update_header_template_code
    vs_paragraph_template: str = crud_views_settings.update_paragraph_template
    vs_paragraph_template_code: str = crud_views_settings.update_paragraph_template_code
    vs_action_label_template: str = crud_views_settings.update_action_label_template
    vs_action_label_template_code: str = crud_views_settings.update_action_label_template_code
    vs_action_short_label_template: str = crud_views_settings.update_action_short_label_template
    vs_action_short_label_template_code: str = crud_views_settings.update_action_short_label_template_code

    vs_message_template: str | None = crud_views_settings.update_message_template
    vs_message_template_code: str | None = crud_views_settings.update_message_template_code

    vs_icon_action = "fa-regular fa-pen-to-square"


class UpdateViewPermissionRequired(ViewSetViewPermissionRequiredMixin, UpdateView):  # this file
    vs_permission = "change"
