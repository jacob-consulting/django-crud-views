from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import ViewSetView, ViewSetViewPermissionRequiredMixin


class CreateView(ViewSetView, generic.CreateView):
    template_name = "crud_views/view_create.html"

    cv_key = "create"
    cv_object = False
    cv_path = "create"
    cv_success_key = "list"
    cv_context_actions = crud_views_settings.create_context_actions

    # texts and labels
    cv_header_template: str | None = crud_views_settings.create_header_template
    cv_header_template_code: str | None = crud_views_settings.create_header_template_code
    cv_paragraph_template: str | None = crud_views_settings.create_paragraph_template
    cv_paragraph_template_code: str | None = crud_views_settings.create_paragraph_template_code
    cv_action_label_template: str | None = crud_views_settings.create_action_label_template
    cv_action_label_template_code: str | None = crud_views_settings.create_action_label_template_code
    cv_action_short_label_template: str | None = crud_views_settings.create_action_short_label_template
    cv_action_short_label_template_code: str | None = crud_views_settings.create_action_short_label_template_code

    cv_message_template: str | None = crud_views_settings.create_message_template
    cv_message_template_code: str | None = crud_views_settings.create_message_template_code

    cv_icon_action = "fa-regular fa-square-plus"

    def form_valid(self, form):
        """
        Set parent model instance at form instance
        """

        parent_model = self.cv.get_parent_model()
        if parent_model:
            attr = self.cv.get_parent_attributes(first_only=True)
            arg = self.cv.get_parent_url_args(first_only=True)
            pk = self.kwargs[arg]
            parent = get_object_or_404(parent_model, pk=pk)
            setattr(form.instance, attr, parent)

        return super().form_valid(form)


class CreateViewPermissionRequired(ViewSetViewPermissionRequiredMixin, CreateView):  # this file
    cv_permission = "add"
