from django.utils.translation import gettext_lazy as _
from django.views import generic

from crud_views.lib.view import ViewSetView, ViewSetViewPermissionRequiredMixin
from crud_views.lib.settings import crud_views_settings


class UpdateView(ViewSetView, generic.UpdateView):
    template_name = "crud_views/view.update.html"

    cv_key = "update"
    cv_path = "update"
    cv_success_key = "list"
    cv_context_actions = crud_views_settings.update_context_actions

    # texts and labels
    cv_header_template: str = crud_views_settings.update_header_template
    cv_header_template_code: str = crud_views_settings.update_header_template_code
    cv_paragraph_template: str = crud_views_settings.update_paragraph_template
    cv_paragraph_template_code: str = crud_views_settings.update_paragraph_template_code
    cv_action_label_template: str = crud_views_settings.update_action_label_template
    cv_action_label_template_code: str = crud_views_settings.update_action_label_template_code
    cv_action_short_label_template: str = crud_views_settings.update_action_short_label_template
    cv_action_short_label_template_code: str = crud_views_settings.update_action_short_label_template_code

    cv_message_template: str | None = crud_views_settings.update_message_template
    cv_message_template_code: str | None = crud_views_settings.update_message_template_code

    cv_icon_action = "fa-regular fa-pen-to-square"


class UpdateViewPermissionRequired(ViewSetViewPermissionRequiredMixin, UpdateView):  # this file
    cv_permission = "change"
